import pandas as pd
from comet_ml import Experiment
from feature_engineering import FeatureEngineer
from train_evaluation import Evaluator, Trainer
from utils import compare_models, load_models, log_model_results

from tools.logging_config import logger
from tools.ohlc_data_reader import OhlcDataReader
from tools.settings import SupportedCoins, settings

FEATURE_ENGINEER_CONFIG = "src/configs/config.yaml"
BASELINE_MODEL_CONFIG = "src/configs/baseline_config.yaml"
CHALLENGER_MODEL_CONFIG = "src/configs/challenger_config.yaml"


def main(
    feature_view_name: str,
    feature_view_version: int,
    product_id: list[str],
    last_n_days_to_fetch_from_store: int,
    last_n_days_to_test_model: int,
    prediction_window_tick: int,
):
    """Run main pipeline to generate price predictions.

    The model follows the following steps:
    1. Fetch OHLC data from the feature store.
    2. Create the target variable.
    3. Train the model.
    4. Generate predictions with baseline model
    5. Compare model predictions vs baseline model predictions.


    Args:
    ----
    feature_view_name: The name of the feature view.
    feature_view_version: The version of the feature view.
    product_id: The product_id to read data for.
    last_n_days_to_fetch_from_store: The number of days to read data from.
    last_n_days_to_test_model: The number of days to test the model on.
    prediction_window_tick: The prediction window tick into the future.

    """
    # Create experiment to log metadata to CometML
    experiment = Experiment(
        api_key=settings.comet_ml.api_key,
        project_name=settings.comet_ml.project_name,
        workspace=settings.comet_ml.workspace,
    )
    experiment.log_parameters(
        {
            "feature_view_name": feature_view_name,
            "feature_view_version": feature_view_version,
            "product_id": product_id,
            "last_n_days_to_fetch_from_store": last_n_days_to_fetch_from_store,
            "last_n_days_to_test_model": last_n_days_to_test_model,
            "prediction_window_tick": prediction_window_tick,
        }
    )
    # Step 1 - Fetch OHLC data
    ohlc_data_reader = OhlcDataReader(
        feature_view_name=feature_view_name,
        feature_view_version=feature_view_version,
    )
    ohlc_data = ohlc_data_reader.read_from_offline_store(
        product_id=product_id,
        last_n_days=last_n_days_to_fetch_from_store,
    )
    experiment.log_dataset_hash(ohlc_data)

    logger.info("Splitting data into train and test sets.")
    train_df, test_df = temporal_train_test_split(
        ohlc_data, last_n_days_to_test_model=last_n_days_to_test_model
    )
    experiment.log_metric("n_rows_train", train_df.shape[0])
    experiment.log_metric("n_rows_test", test_df.shape[0])

    logger.info("Creating target variable for trainset.")
    train_df = create_target_variable(train_df, prediction_window_tick)
    logger.info("Creating target variable for testset.")
    test_df = create_target_variable(test_df, prediction_window_tick)
    logger.info(
        "--------Train / Test split ----------- \n"
        f"Train: {train_df["product_id"].count()}\n"
        f"Test: {test_df["product_id"].count()}\n"
    )
    # log_target_distribution(train_df, test_df, experiment)
    # Split into features and target for each set
    X_train, y_train = train_df.drop("target", axis=1), train_df["target"]
    X_test, y_test = test_df.drop("target", axis=1), test_df["target"]

    # Add Features based on some feature engineering
    logger.info("Feature engineering pipeline.")
    feature_engineering = FeatureEngineer(FEATURE_ENGINEER_CONFIG)
    X_train_features = feature_engineering.add_features(X_train)
    X_test_features = feature_engineering.add_features(X_test)
    experiment.log_metric("X_train_shape", X_train_features.shape)
    experiment.log_metric("y_train_shape", y_train.shape)
    experiment.log_metric("X_test_shape", X_test_features.shape)
    experiment.log_metric("y_test_shape", y_test.shape)

    logger.info("Evaluating performance of baseline models")
    baseline_models = load_models(BASELINE_MODEL_CONFIG)

    logger.info("Evaluating baseline models")
    baseline_trainer = Trainer(baseline_models)
    trained_baselines = baseline_trainer.train_all_models(
        X_train,
        y_train,
        pct_change_train_mean=(
            X_train["pct_change"].mean() if "pct_change" in X_train else 0
        ),
    )
    evaluator = Evaluator(metrics=["MAE", "MAPE"])
    baseline_metrics_train = evaluator.evaluate_all_models(
        trained_baselines, X_train, y_train
    )
    logger.info(f"Train Baseline metrics: {baseline_metrics_train}")
    baseline_metrics_test = evaluator.evaluate_all_models(
        trained_baselines, X_test, y_test
    )
    logger.info(f"Test Baseline metrics: {baseline_metrics_test}")
    log_model_results("TEST", baseline_metrics_test, experiment)
    best_baseline = compare_models(baseline_metrics_test, "MAPE")
    logger.info(
        f"Best baseline by MAPE = {best_baseline} with "
        f"{baseline_metrics_test[best_baseline]}"
    )

    logger.info("Evaluating the performance of challenger models")
    challenger_models = load_models(CHALLENGER_MODEL_CONFIG)
    challenger_trainer = Trainer(challenger_models)
    trained_challengers = challenger_trainer.train_all_models(
        X_train_features, y_train
    )
    challenger_metrics_train = evaluator.evaluate_all_models(
        trained_challengers, X_train_features, y_train
    )
    logger.info(f"Train Challenger metrics: {challenger_metrics_train}")
    challenger_metrics_test = evaluator.evaluate_all_models(
        trained_challengers, X_test_features, y_test
    )
    logger.info(f"Test Challenger metrics: {challenger_metrics_test}")
    log_model_results("TEST", challenger_metrics_test, experiment)
    best_challenger = compare_models(challenger_metrics_test, "MAPE")
    logger.info(
        f"Best challenger by MAPE = {best_challenger} with "
        f"{challenger_metrics_test[best_challenger]}"
    )


def temporal_train_test_split(
    ohlc_data: pd.DataFrame, last_n_days_to_test_model: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the data into train and test splits.

    Split is a temporal split. Last_n_days_to_test_model define
    the number of days for testing the model.

    Args:
    ----
    ohlc_data: The OHLC data to split.
    last_n_days_to_test_model: The number of days to test the model on.

    """
    max_data_in_dataset = ohlc_data["end_time"].max()
    cutoff_date = max_data_in_dataset - pd.Timedelta(
        days=last_n_days_to_test_model
    )
    train_df = ohlc_data[ohlc_data["end_time"] < cutoff_date]
    test_df = ohlc_data[ohlc_data["end_time"] >= cutoff_date]
    return train_df, test_df


def create_target_variable(
    ohlc_data: pd.DataFrame,
    prediction_window_tick: int,
) -> pd.DataFrame:
    """Create the target variable based on future close percentage changes.

    The target variable is generated by comparing the percentage change in the
    close price of the current tick with the close price of a future tick,
    defined by `prediction_window_tick`.

    Args:
    ----
    ohlc_data: The OHLC data to create the target variable for.
    prediction_window_tick: The number of ticks in the future to compare

    """
    ohlc_data["pct_change"] = (
        ohlc_data.groupby("product_id")["close"].pct_change(
            periods=prediction_window_tick
        )
        * 100
    )
    ohlc_data.loc[:, "pct_change"].fillna(0, inplace=True)
    ohlc_data["target"] = ohlc_data.groupby("product_id")["pct_change"].shift(
        -prediction_window_tick
    )
    return ohlc_data.dropna(subset=["target"])


if __name__ == "__main__":
    main(
        feature_view_name="ohlc_feature_view",
        feature_view_version=1,
        product_id=[SupportedCoins.BTC_USD.value, SupportedCoins.ETH_USD.value],
        last_n_days_to_fetch_from_store=90,
        last_n_days_to_test_model=30,
        prediction_window_tick=1,
    )

import pandas as pd
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from tools.logging_config import logger


class MultiLinearRegression:
    """Multi Linear Regression model."""

    def __init__(self, prediction_horizon: int = 1, **kwargs) -> None:
        """Initialize the Multi Linear Regression model.

        Args:
        ----
        prediction_horizon (int): Number of steps to forecast ahead.
        **kwargs: Additional arguments for the LinearRegression model.

        """
        self.prediction_horizon = prediction_horizon

    def train(
        self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs
    ) -> None:
        """Train the model.

        Args:
        ----
        X_train (pd.DataFrame): Training features.
        y_train (pd.Series): Training labels.
        kwargs: keyword arguments for train other models.

        """
        numeric_features = X_train.select_dtypes(
            include=["int64", "float64"]
        ).columns.tolist()
        categorical_features = X_train.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), numeric_features),
                (
                    "cat",
                    OneHotEncoder(handle_unknown="ignore"),
                    categorical_features,
                ),
            ]
        )

        self.pipeline = Pipeline(
            [("preprocessor", preprocessor), ("regressor", LinearRegression())]
        )
        logger.info("Training model...")
        self.pipeline.fit(X_train, y_train)

    def predict(self, test_df: pd.DataFrame) -> pd.DataFrame:
        """Generate predictions.

        Args:
        ----
        test_df (pd.DataFrame): Test features.

        """
        logger.info("Generating predictions...")
        test_df = test_df.copy()
        predictions = self.pipeline.predict(test_df)
        test_df[f"forecast_{self.prediction_horizon}"] = predictions
        return test_df


class XGBoostModel:
    """XGBoost model."""

    def __init__(self, prediction_horizon: int = 1, **kwargs) -> None:
        """Initialize the XGBoost model.

        Args:
        ----
        prediction_horizon (int): Number of steps to forecast ahead.
        **kwargs: Additional arguments for the XGBRegressor model.

        """
        self.prediction_horizon = prediction_horizon
        self.params = kwargs

    def train(
        self, X_train: pd.DataFrame, y_train: pd.Series, boosting_rounds: int
    ) -> None:
        """Train the model.

        Args:
        ----
        X_train (pd.DataFrame): Training features.
        y_train (pd.Series): Training labels.
        boosting_rounds (int): Number of boosting rounds.

        """
        logger.info("Training model...")
        dtrain = xgb.DMatrix(X_train, label=y_train, enable_categorical=True)
        self.model = xgb.train(
            self.params,
            dtrain,
            num_boost_round=boosting_rounds,
            evals=[(dtrain, "train")],
        )

    def predict(self, test_df: pd.DataFrame) -> pd.DataFrame:
        """Generate predictions.

        Args:
        ----
        test_df (pd.DataFrame): Test features.

        """
        logger.info("Generating predictions...")
        dtest = xgb.DMatrix(test_df, enable_categorical=True)
        preds = self.model.predict(dtest)
        test_df[f"forecast_{self.prediction_horizon}"] = preds
        return test_df

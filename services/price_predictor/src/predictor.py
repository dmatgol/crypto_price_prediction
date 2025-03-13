import json
import pickle
from collections import OrderedDict
from typing import Any

import pandas as pd
from comet_ml import Experiment
from comet_ml.api import API
from pydantic import BaseModel
from src.feature_engineering import FeatureEngineer

from tools.logging_config import logger
from tools.ohlc_data_reader import OhlcDataReader
from tools.settings import settings

FEATURE_ENGINEER_CONFIG = "src/configs/config.yaml"


def restore_feature_config(experiment: Experiment) -> OrderedDict:
    """Restore the original feature config structure from CometML parameters.

    This function retrieves the feature config from CometML and restores the
    original structure by removing the order indices from keys and maintaining
    the original order.

    Args:
    ----
    experiment: CometML experiment instance

    Returns:
    -------
    OrderedDict: Feature configuration with original keys in original order

    """
    features_config = experiment.get_parameters_summary("feature_config")[
        "valueCurrent"
    ]
    features_config = json.loads(features_config)
    if not features_config:
        raise ValueError("Feature config not found in experiment parameters")
    # Sort by the numeric prefix to maintain order
    ordered_items = sorted(features_config.items(), key=lambda x: x[0][:2])
    # Remove the numeric prefix and create new OrderedDict
    return OrderedDict(
        (key.split("_", 1)[1], value) for key, value in ordered_items
    )


class PredictorOutput(BaseModel):
    """Pydantic model for the output of the predictor."""

    prediction: float
    product_id: str


class Predictor:
    """Initialize the Predictor class."""

    def __init__(
        self,
        model_path: str,
        feature_view_name: str,
        feature_view_version: int,
        product_id: str,
        features_config: dict[str, Any],
    ) -> None:
        """Initialize the Predictor class.

        Args:
        ----
        model_path: Path to the model.
        feature_view_name: Name of the feature view.
        feature_view_version: Version of the feature view.
        product_id: product id.
        features_config: Dict of features to use for prediction.

        """
        self.model = self._load_model_pickle(model_path)
        logger.info("Model loaded")
        self.ohlc_data_reader = OhlcDataReader(
            feature_view_name=feature_view_name,
            feature_view_version=feature_view_version,
        )
        self.product_id = product_id
        self.features_config = features_config

    @classmethod
    def load_from_model_registry(
        cls, product_id: str, status: str
    ) -> "Predictor":
        """Fetch the model artifact from the model registry.

        It contains all the model and all the relevant metadata needed
        to make predictions from this model artifact and return a Predictor
        object.

        Args:
        ----
        product_id (str): product_id of the model.
        status (str): status of the model (e.g., production).

        """
        comet_api = API(settings.comet_ml.credentials.api_key)
        # Set 1: Get model details
        model = comet_api.get_model(
            workspace=settings.comet_ml.credentials.workspace,
            model_name=settings.comet_ml.general_config.name_model,
        )
        model_versions = model.find_versions(status=status)
        model_version = sorted(model_versions, key=lambda x: x, reverse=True)[0]
        model.download(
            version=model_version,
            output_folder=settings.comet_ml.general_config.output_folder,
        )
        # Set 2: Get experiment key
        experiment_key = model.get_details(version=model_version)[
            "experimentKey"
        ]
        # Set 3: Get experiment parameters
        experiment = comet_api.get_experiment_by_key(experiment_key)
        # We have a specific feature view for the inference that is not related
        # with training. Reason is that for online store, we don't know the
        # timestamp of each bar, so we can't use
        # (product_id, bar_start_timestamp) as a unique key. The solution
        # is to use one feature_view specific for online and that
        # has the product_id as a feature.
        feature_view_name = settings.app_settings.inference_feature_view
        feature_view_version = (
            settings.app_settings.inference_feature_view_version
        )
        # Get remaining parameters from comet_ml
        features_config = restore_feature_config(experiment)
        model_path = (
            settings.comet_ml.general_config.output_folder
            + settings.comet_ml.general_config.name_model
            + ".pkl"
        )
        logger.info(f"Model path: {model_path}")
        return cls(
            model_path=model_path,
            feature_view_name=feature_view_name,
            feature_view_version=feature_view_version,
            product_id=product_id,
            features_config=features_config,
        )

    def _load_model_pickle(self, model_path: str):
        """Load a pickled model from disk."""
        with open(model_path, "rb") as f:
            return pickle.load(f)

    def predict(self) -> PredictorOutput:
        """Generate predictions.

        Steps:
        ----
        1. Fetch the latest data from feature store.
        2. Preprocess features exactly as the model was trained on.
        3. Generate predictions.
        4. Return the predictions.

        """
        logger.info("Fetching data from the feature store")
        ohlc_data = self.ohlc_data_reader.read_from_online_store(
            product_id=self.product_id
        )
        ohlc_data_dict = json.loads(ohlc_data[1])
        ohlc_data_df = pd.DataFrame(ohlc_data_dict)
        ohlc_data_df = ohlc_data_df.assign(
            start_time=pd.to_datetime(ohlc_data_df["start_time"], utc=True),
            end_time=pd.to_datetime(ohlc_data_df["end_time"], utc=True),
        )
        logger.info("Creating features for inference")
        feature_engineering = FeatureEngineer(config=self.features_config)
        features = feature_engineering.add_features(ohlc_data_df)
        logger.info("Generating predictions")
        prediction = self.model.predict(features)
        return prediction.iloc[-1]


if __name__ == "__main__":

    predictor = Predictor.load_from_model_registry(
        product_id="LTC-USD",
        status=settings.comet_ml.general_config.status,
    )
    predictions = predictor.predict()
    logger.info(f"Predictions: {predictions}")

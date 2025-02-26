import json
import pickle

import pandas as pd
from feature_engineering import FeatureEngineer
from pydantic import BaseModel

from tools.logging_config import logger
from tools.ohlc_data_reader import OhlcDataReader

FEATURE_ENGINEER_CONFIG = "services/price_predictor/src/configs/config.yaml"


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
    ) -> None:
        """Initialize the Predictor class.

        Args:
        ----
        model_path: Path to the model.
        feature_view_name: Name of the feature view.
        feature_view_version: Version of the feature view.
        product_id: product id.

        """
        self.model = self._load_model_pickle(model_path)
        self.ohlc_data_reader = OhlcDataReader(
            feature_view_name=feature_view_name,
            feature_view_version=feature_view_version,
        )
        self.product_id = product_id

    def _load_model_pickle(self, model_path: str):
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
        ohlc_data_dict = json.loads(ohlc_data)
        ohlc_data_df = pd.DataFrame(ohlc_data_dict)
        logger.info("Creating features for inference")
        feature_engineering = FeatureEngineer(FEATURE_ENGINEER_CONFIG)
        features = feature_engineering.add_features(ohlc_data_df)
        logger.info("Generating predictions")
        prediction = self.model.predict(features)
        return prediction


if __name__ == "__main__":
    predictor = Predictor(
        model_path="services/price_predictor/MultiLinearRegression_return_predictor.pkl",
        feature_view_name="online_feature_view",
        feature_view_version=1,
        product_id="LTC-USD",
    )
    predictor.predict()

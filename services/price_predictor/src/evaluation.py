from typing import Any

import pandas as pd
import yaml
from sklearn.metrics import mean_absolute_error

from tools.logging_config import logger  # isort: skip

from models.baseline_models import MovingAverageBaseline  # isort: skip
from models.baseline_models import TrainMeanPctChangeBaseline  # isort: skip

MODEL_CLASSES = {
    "MovingAverageBaseline": MovingAverageBaseline,
    "TrainMeanPctChangeBaseline": TrainMeanPctChangeBaseline,
}


class ModelTester:
    """Class to test baseline models against a challenger model."""

    def __init__(
        self, baseline_config_path: str, challenger_config_path: str = None
    ) -> None:
        """Initialize the ModelTester class.

        Args:
        ----
        baseline_config_path (str): Baseline model config with hyperparameters.
        challenger_config_path (str): Chal model config with hyperparameters.

        """
        self.challenger_model = self._load_models(challenger_config_path)
        self.baseline_model = self._load_models(baseline_config_path)

    def _load_config(self, config_path: str) -> dict[str, Any]:
        """Load feature configuration from a YAML file."""
        with open(config_path) as file:
            return yaml.safe_load(file)

    def _load_models(self, config_path: str) -> dict[str, Any]:
        """Load models from configuration."""
        if config_path is None:
            return {}

        config = self._load_config(config_path)
        models = {}
        for model_config in config["models"]:
            model_name = model_config["model"]
            model_args = model_config.get("model_args", {})
            model_class = MODEL_CLASSES[model_name]  # Get the class by name
            models[model_name] = model_class(**model_args)
        return models

    def test_baseline_model(
        self, X_test: pd.DataFrame, y_test: pd.Series, **kwargs
    ) -> None:
        """Test baseline models."""
        logger.info("Testing Baseline Models")
        for model_name, model in self.baseline_model.items():
            self.test_model(model_name, model, X_test, y_test, **kwargs)

    def test_challenger_model(
        self, X_test: pd.DataFrame, y_test: pd.Series, **kwargs
    ) -> None:
        """Test challenger models."""
        logger.info("Testing Challenger Models")
        for model_name, model in self.challenger_model.items():
            self.test_model(model_name, model, X_test, y_test, **kwargs)

    def test_model(
        self,
        model_name: str,
        model: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        **kwargs,
    ) -> None:
        """Test a model.

        Args:
        ----
        model_name (str): Name of the model.
        model (Any): Model to test.
        X_test (pd.DataFrame): Test features.
        y_test (pd.Series): Test labels.
        **kwargs: Additional keyword arguments for model-specific setup.

        """
        logger.info(f"Testing {model_name}")
        if isinstance(model, TrainMeanPctChangeBaseline):
            # Set the train mean dynamically
            model.set_train_mean(kwargs.get("pct_change_train_mean"))
        predictions = model.predict(test_df=X_test)
        prediction_horizon = model.prediction_horizon
        mae = mean_absolute_error(
            y_test, predictions[f"forecast_{prediction_horizon}"]
        )
        logger.info(f"{model_name} Mean Absolute Error: {mae}")

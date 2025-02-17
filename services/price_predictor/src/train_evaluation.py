from typing import Any

import numpy as np
import pandas as pd


class Trainer:
    """Class to handle the training of one or multiple models."""

    def __init__(self, models: dict[str, Any]) -> None:
        """Initialize the Trainer class.

        Args:
        ----
        models (dict[str, Any]): Dictionary of models to train.

        """
        self.models = models

    def train_all_models(
        self, X_train: pd.DataFrame, y_train: pd.Series, **kwargs
    ) -> dict[str, Any]:
        """Train all models and return a dictionary of trained models."""
        trained_models = {}
        for model_name, model in self.models.items():
            if hasattr(model, "train"):
                model.train(X_train, y_train, **kwargs)
            trained_models[model_name] = model
        return trained_models


class Evaluator:
    """Class to evaluate trained models on a given dataset."""

    def __init__(self, metrics: list[str] = None) -> None:
        """Initialize the Evaluator class.

        Args:
        ----
        metrics: List of metrics to calculate. Defaults to ["MAE", "MAPE"].

        """
        self.metrics = metrics or ["MAE", "MAPE"]

    def evaluate_all_models(
        self,
        models: dict[str, Any],
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> dict[str, dict[str, float]]:
        """Evaluate a set of models and return its performance."""
        all_metrics = {}
        for name, model in models.items():
            all_metrics[name] = self.evaluate_model(model, X_test, y_test)
        return all_metrics

    def evaluate_model(
        self,
        model: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> dict[str, float]:
        """Test a model.

        Args:
        ----
        model_name (str): Name of the model.
        model (Any): Model to test.
        X_test (pd.DataFrame): Test features.
        y_test (pd.Series): Test labels.
        **kwargs: Additional keyword arguments for model-specific setup.

        """
        predictions_df = model.predict(X_test=X_test)
        horizon_col = f"forecast_{getattr(model, 'prediction_horizon', 1)}"
        predictions = predictions_df[horizon_col]
        mae = np.mean(np.abs(y_test - predictions))
        mean_abs_target = np.mean(np.abs(y_test))
        mape = (mae / mean_abs_target) * 100

        results = {}
        if "MAE" in self.metrics:
            results["MAE"] = mae
        if "MAPE" in self.metrics:
            results["MAPE"] = mape

        return results

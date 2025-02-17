import os
import pickle
import tempfile
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import yaml
from comet_ml import Experiment

from models.shallow_models import MultiLinearRegression  # isort:skip
from models.shallow_models import XGBoostModel  # isort:skip

from models.baseline_models import MovingAverageBaseline  # isort:skip
from models.baseline_models import TrainMeanPctChangeBaseline  # isort:skip
from tools.logging_config import logger  # isort:skip

MODEL_CLASSES = {
    "MovingAverageBaseline": MovingAverageBaseline,
    "TrainMeanPctChangeBaseline": TrainMeanPctChangeBaseline,
    "XGBoostModel": XGBoostModel,
    "MultiLinearRegression": MultiLinearRegression,
}


def log_model_results(
    mode: str,
    model_results: dict[str, dict[str, float]],
    experiment: Experiment,
):
    """Log model results in COMET ML."""
    for model_name, m_dict in model_results.items():
        experiment.log_metrics(m_dict, prefix=f"{mode}/{model_name}")


def log_target_distribution(
    train_df: pd.DataFrame, test_df: pd.DataFrame, experiment: Experiment
) -> None:
    """Log distribution of target variable for train and test sets."""
    for dataset_name, df in [("Train", train_df), ("Test", test_df)]:
        for product_id in df["product_id"].unique():
            target_distribution = plot_pct_change_distribution(df, product_id)

            with tempfile.NamedTemporaryFile(
                suffix=".png", delete=False
            ) as tmpfile:
                target_distribution.savefig(tmpfile.name, bbox_inches="tight")
                plt.close(target_distribution)  # Close the plot to free memory

                # Log the figure to Comet.ml
                experiment.log_image(
                    tmpfile.name,
                    name=f"{dataset_name}_{product_id}_target_distribution.png",
                )

            # Clean up the temporary file
            os.unlink(tmpfile.name)


def log_best_model(
    model: Any,
    model_name: str,
    best_baseline_metric: float,
    best_challenger_metric: float,
    experiment: Experiment,
) -> None:
    """Log the best model.

    Args:
    ----
    model (Any): Model to log
    model_name (str): Model name
    best_baseline_metric (float): Best baseline metric
    best_challenger_metric (float): Best challenger metric
    experiment (Experiment): Comet ML experiment

    """
    with open(f"./{model_name}_return_predictor.pkl", "wb") as f:
        logger.info("Logging best model...")
        pickle.dump(model, f)

    experiment.log_model(
        name=model_name, file_or_folder=f"./{model_name}_return_predictor.pkl"
    )
    if best_baseline_metric > best_challenger_metric:
        logger.info("Pushing model to Comet ML...")
        experiment.register_model(model_name=f"{model_name}_return_predictor")


def compare_models(
    metrics_dict: dict[str, dict[str, float]], metric_name: str = "MAE"
) -> str:
    """Compare models given a specific metric and returns the best model."""
    best_model = None
    best_val = float("inf")

    for model_name, m_dict in metrics_dict.items():
        current_val = m_dict.get(metric_name, float("inf"))
        if current_val < best_val:
            best_val = current_val
            best_model = model_name

    return best_model


def load_models(config_path: str) -> dict[str, Any]:
    """Load models from configuration."""
    if config_path is None:
        return {}

    with open(config_path) as file:
        config = yaml.safe_load(file)
    models = {}
    for model_config in config["models"]:
        model_name = model_config["model"]
        model_args = model_config.get("model_args", {})
        model_class = MODEL_CLASSES[model_name]  # Get the class by name
        models[model_name] = model_class(**model_args)
    return models


def plot_pct_change_distribution(
    df: pd.DataFrame, product_id: str
) -> plt.Figure:
    """Calculate and plot the distribution of percentage changes.

    Args:
    ----
    df: pd.DataFrame
        DataFrame containing the percentage changes.
    product_id: str
        Product ID for which to plot the distribution.

    """
    # Calculate mean and standard deviation
    mean_pct_change = df["target"].mean()

    # Plot the distribution
    sns.histplot(df["target"], kde=True)  # kde=True adds a smooth density curve
    plt.axvline(
        mean_pct_change,
        color="red",
        linestyle="--",
        label=f"Mean: {mean_pct_change:.2f}%",
    )
    plt.axvline(0, color="orange", linestyle="--", label="0: 0%")
    plt.axvline(
        0.1, color="green", linestyle="--", label="Upper Threshold: 0.1%"
    )
    plt.axvline(
        -0.1, color="blue", linestyle="--", label="Lower Threshold: -0.1%"
    )

    plt.title(f"Distribution of Values of {product_id}")
    plt.xlabel("Values")
    plt.ylabel("Frequency")
    plt.legend()
    return plt

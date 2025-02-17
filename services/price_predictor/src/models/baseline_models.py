import numpy as np
import pandas as pd


class TrainMeanPctChangeBaseline:
    """Baseline model that predicts the next close bar price.

    Prediction is set to be the mean pct change of the close prices seen in
    train data.
    """

    def __init__(self, prediction_horizon: int = 1) -> None:
        """Initialize Train pct change mean baseline.

        Args:
        ----
        train_mean (float): Mean of close price pct change on train data.
        prediction_horizon (int): Number of steps to forecast ahead.

        """
        self.prediction_horizon = prediction_horizon

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.DataFrame,
        pct_change_train_mean: float,
    ) -> None:
        """Set the mean pct change of the train data.

        Args:
        ----
        X_train: pd.DataFrame: Train data.
        y_train: pd.DataFrame: Train labels.
        pct_change_train_mean (float): Mean pct change of the train data.

        """
        self.pct_change_train_mean = pct_change_train_mean

    def predict(self, X_test: pd.DataFrame) -> pd.DataFrame:
        """Predict based on the mean pct change seen in train data."""
        df_ = X_test.copy()
        df_[f"forecast_{self.prediction_horizon}"] = self.pct_change_train_mean
        return df_


class MovingAverageBaseline:
    """Enhanced Moving Average (SMA) baseline using only test data."""

    def __init__(self, window_size: int, prediction_horizon: int = 1):
        """Initialize moving average baseline model.

        Args:
        ----
        window_size (int): Size of the moving average window.
        prediction_horizon (int): Number of steps to forecast ahead.

        """
        self.window_size = window_size
        self.prediction_horizon = prediction_horizon

    def predict(self, X_test: pd.DataFrame) -> pd.Series:
        """Generate moving average predictions using only test data.

        Args:
        ----
        X_test (pd.DataFrame): DataFrame containing test data.

        """
        test_df = X_test.copy()

        for product in test_df["product_id"].unique():
            product_df = test_df[test_df["product_id"] == product].sort_values(
                "start_time"
            )
            product_df = self._compute_forecasts(product_df)

            # Update the original test_df with the forecast columns
            for h in range(1, self.prediction_horizon + 1):
                test_df.loc[product_df.index, f"close_forecast_{h}"] = (
                    product_df[f"close_forecast_{h}"]
                )
                test_df.loc[product_df.index, f"forecast_{h}"] = product_df[
                    f"forecast_{h}"
                ]

        return test_df

    def _compute_forecasts(self, group: pd.DataFrame) -> pd.DataFrame:
        """Compute forecasts for a single product group."""
        group = group.copy()
        close_prices = group["close"].values
        forecasts = []

        for i in range(len(close_prices)):
            # Get available history up to current index
            available_data = close_prices[
                max(0, i - self.window_size + 1) : i + 1
            ]

            # Compute base forecast
            if len(available_data) == 0:
                base_forecast = close_prices[i]  # Fallback to current price
            else:
                base_forecast = np.mean(available_data)

            # Generate multi-step forecasts
            horizon_forecasts = [base_forecast]
            for _ in range(1, self.prediction_horizon):
                available_data = np.append(
                    available_data, horizon_forecasts[-1]
                )
                available_data = available_data[-self.window_size :]
                horizon_forecasts.append(np.mean(available_data))

            forecasts.append(horizon_forecasts)

        # Add forecasts to dataframe
        for h in range(self.prediction_horizon):
            group[f"close_forecast_{h + 1}"] = [f[h] for f in forecasts]
            group[f"forecast_{h + 1}"] = (
                (group[f"close_forecast_{h + 1}"] - group["close"])
                / group["close"]
                * 100
            )

        return group

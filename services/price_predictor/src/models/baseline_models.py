import numpy as np
import pandas as pd


class TrainMeanPctChangeBaseline:
    """Baseline model that predicts the next close bar price.

    Prediction is set to be the mean pct change of the close prices seen in
    train data.
    """

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predict based on the mean pct change seen in train data."""
        df_ = df.copy()
        df_["prediction"] = df_["pct_change"].mean()
        return df_["prediction"]


class MovingAverageBaseline:
    """Simple Moving Average (SMA) baseline."""

    def __init__(self, window_size: int, prediction_horizon: int = 1):
        """Initialize moving average baseline model.

        Args:
        ----
        window_size (int): Size of the moving average window.
        prediction_horizon (int): Prediction horizon.

        """
        self.window_size = window_size
        self.prediction_horizon = prediction_horizon

    def predict(
        self, test_df: pd.DataFrame, train_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Predict the moving average of the closing price.

        Args:
        ----
        test_df (pd.DataFrame): The dataframe to predict on.
        train_df (pd.DataFrame): The train dataframe to use for the initial n
        steps, where n < self.window_size to ensure that we have enough data.

        """
        forecasted_results = []

        # Process each product_id separately.
        for product in test_df["product_id"].unique():
            # Get train and test data for the product, sorted by time.
            train_prod = train_df[
                train_df["product_id"] == product
            ].sort_values("start_time")
            test_prod = test_df[test_df["product_id"] == product].sort_values(
                "start_time"
            )

            # Take the most recent 'window' rows from train as the seed.
            seed = train_prod.tail(self.window_size)

            # Concatenate seed and test data.
            combined = pd.concat([seed, test_prod]).sort_values("start_time")

            # Compute forecasts on the combined DataFrame.
            combined_with_forecasts = self.compute_forecasts_for_group(combined)

            # Drop the seed rows. We drop the first 'window' rows from the
            # combined DataFrame.
            forecast_for_test = combined_with_forecasts.iloc[self.window_size :]
            forecasted_results.append(forecast_for_test)

        forecasted_df = pd.concat(forecasted_results)
        return forecasted_df[f"forecast_{self.prediction_horizon}"]

    def compute_forecasts_for_group(
        self,
        group: pd.DataFrame,
    ) -> pd.DataFrame:
        """Compute an iterative forecast (of horizon n_forecast).

        For each row in the group, compute an iterative forecast
        (of horizon n_forecast) based on all historical pct_change values up to
        that time. The forecasts for each row will be stored in new columns:
        forecast_1, forecast_2, ...

        Args:
        ----
        group (pd.Series): Pandas DataFrame with historical close prices.

        """
        group = group.copy()
        # Create empty lists to hold forecasts for each horizon.
        forecast_data: dict[str, list[float]] = {
            f"forecast_{i + 1}": [] for i in range(self.prediction_horizon)
        }

        # Iterate over the DataFrame rows in order.
        for idx in group.index:
            # Get historical close prices from the start up to and including
            # the current row. Assumes the DataFrame is sorted by time.
            historical = group.loc[:idx, "close"]
            # Compute the iterative forecast.
            forecasts = self.iterative_forecast_for_row(historical)
            # Save each forecast.
            for i in range(self.prediction_horizon):
                pct_change = (
                    (group.loc[idx, "close"] - forecasts[i])
                    / group.loc[idx, "close"]
                    * 100
                )
                forecast_data[f"forecast_{i + 1}"].append(pct_change)

        # Append the forecast columns to the group DataFrame.
        for col, values in forecast_data.items():
            group[col] = values
        return group

    def iterative_forecast_for_row(self, historical: pd.Series) -> list[float]:
        """Forecast n steps into the future for each row element.

        Given a sequence of historical close prices, forecast n_forecast future
        values.
        The forecast procedure is:
        - For the first forecast, use the average of the last `window` values
        (or all if fewer).
        - Append that forecast to the history and compute the next forecast
        using the last `window` values.

        Args:
        ----
        historical (pd.Series): Pandas Series with historical close prices.

        """
        hist = list(historical)  # convert to list
        forecasts = []
        for _ in range(self.prediction_horizon):
            # Get last n historical values
            window_data = (
                hist[-self.window_size :]
                if len(hist) >= self.window_size
                else hist
            )
            # Forecast close price as mean of last window values
            forecast = np.mean(window_data) if window_data else np.nan
            forecasts.append(forecast)
            # Update history with the forecast for the next iteration
            hist.append(forecast)
        return forecasts

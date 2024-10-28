import pandas as pd


class TrainMeanPctChangeBaseline:
    """Baseline model that predicts the next close bar price.

    Prediction is set to be the mean pct change of the close prices seen in
    train data.
    """

    def __init__(self, mean_pct_change: float):
        """Initialize TrainMeanPctChange baseline model.

        Args:
        ----
        mean_pct_change (float): Mean %change of the close prices
            seen in train data.

        """
        self.mean_pct_change = mean_pct_change

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predict based on the mean pct change seen in train data."""
        df_ = df.copy()
        df_["prediction"] = self.mean_pct_change
        return df_["prediction"]


class MovingAverageBaseline:
    """Simple Moving Average (SMA) baseline."""

    def __init__(self, window_size: int):
        """Initialize moving average baseline model.

        Args:
        ----
        window_size (int): Size of the moving average window.

        """
        self.window_size = window_size

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predict the moving average of the closing price.

        Args:
        ----
        df (pd.DataFrame): The dataframe to predict on.

        """
        return (
            df["pct_change"]
            .rolling(window=self.window_size)
            .mean()
            .fillna(df["pct_change"].fillna(0))
        )

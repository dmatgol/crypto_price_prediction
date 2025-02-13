from typing import Any

import numpy as np
import pandas as pd
import talib
import yaml

from tools.logging_config import logger


class FeatureEngineer:
    """Flexible feature engineer class for financial time series data.

    Dynamically generate features based on the given data.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        config_path: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the FeatureEngineer class.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.
        config_path (str): The path to the YAML configuration file.
        config (dict[str, Any]): The configuration for the feature engineer.

        """
        self.df = df
        # Load configuration from either a file or a dictionary
        if config is not None:
            self.config = config
        elif config_path is not None:
            self.config = self.load_config(config_path)
        else:
            raise ValueError(
                "Either 'config_path' or 'config' must be provided."
            )

    @staticmethod
    def load_config(config_path):
        """Load feature configuration from a YAML file."""
        with open(config_path) as file:
            return yaml.safe_load(file)

    def add_features(self) -> pd.DataFrame:
        """Add features aggregated per product_id."""
        df = self.df.copy()

        # Group by product_id and apply features to each group separately.
        df_grouped = df.groupby("product_id", group_keys=False).apply(
            self._apply_features_to_group
        )

        return df_grouped

    def _apply_features_to_group(self, group: pd.DataFrame) -> pd.DataFrame:
        """Apply all feature methods defined in the config per product_id."""
        for feature_name, parms in self.config.items():
            method_name = f"add_{feature_name}"
            method = getattr(self, method_name, None)
            if method:
                if isinstance(parms, list):
                    for param in parms:
                        group = (
                            method(group, **param) if parms else method(group)
                        )
                else:
                    group = method(group, **parms) if parms else method(group)
            else:
                logger.debug(f"Method {method_name} not found.")
        return group

    def add_log_return(self, df: pd.DataFrame, n_bars: int) -> pd.DataFrame:
        """Add log return feature to the dataframe.

        Purpose: Capture compounded returns over bars
        """
        aux = df.copy()
        aux.loc[:, "returns"] = df["close"] / df["close"].shift(n_bars)
        for i in range(n_bars):
            aux.loc[i, "returns"] = (
                df["close"].iloc[: i + 1] / df["close"].shift(i).iloc[: i + 1]
            ).iloc[i]

        df.loc[:, f"log_return_{n_bars}"] = np.log(aux["returns"])
        return df

    def add_rsi_indicator(
        self, df: pd.DataFrame, rsi_timeperiod: int | None = 14
    ) -> pd.DataFrame:
        """Add RSI indicator to the dataframe.

        Purpose: Measure the momentum of price movements to identify
        overbought and oversold conditions.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.
        rsi_timeperiod (int): The time period for the RSI indicator.

        """
        df.loc[:, f"rsi_{rsi_timeperiod}"] = talib.RSI(
            df["close"], timeperiod=rsi_timeperiod
        )
        # Progressive filling - assume a minimum of 7 data points
        # otherwise rsi will be always very high.
        mean = df[f"rsi_{rsi_timeperiod}"].mean()
        for i in range(7, rsi_timeperiod):
            df.loc[i, f"rsi_{rsi_timeperiod}"] = talib.RSI(
                df["close"].iloc[: i + 1], timeperiod=i
            ).iloc[-1]
        df.loc[:, f"rsi_{rsi_timeperiod}"].fillna(mean, inplace=True)
        return df

    def add_momentum_indicator(
        self, df: pd.DataFrame, momentum_timeperiod: int | None = 14
    ) -> pd.DataFrame:
        """Add Momentum indicator to the dataframe.

        Purpose: Measure the momentum of price movements to identify
        overbought and oversold conditions.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.
        momentum_timeperiod (int): The time period for the momentum indicator.

        """
        df.loc[:, f"momentum_{momentum_timeperiod}"] = talib.MOM(
            df["close"], timeperiod=momentum_timeperiod
        )
        for i in range(1, momentum_timeperiod):
            df.loc[i, f"momentum_{momentum_timeperiod}"] = talib.MOM(
                df["close"].iloc[: i + 1], timeperiod=i
            ).iloc[-1]
        df[f"momentum_{momentum_timeperiod}"].fillna(0, inplace=True)
        return df

    def add_volatility_indicator(
        self, df: pd.DataFrame, volatility_timeperiod: int | None = 14
    ) -> pd.DataFrame:
        """Add Volatility indicator to the dataframe.

        Purpose: Measure the variability in returns, indicating risk
        and potential future movement.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.
        volatility_timeperiod (int): The time period for the volatility.

        """
        df.loc[:, f"volatility_{volatility_timeperiod}"] = (
            df["pct_change"].rolling(window=volatility_timeperiod).std()
        )
        # Progressive filling
        for i in range(2, volatility_timeperiod):
            df.loc[i, f"volatility_{volatility_timeperiod}"] = (
                df["pct_change"].iloc[1 : i + 1].rolling(i).std().iloc[-1]
            )
        df[f"volatility_{volatility_timeperiod}"].fillna(0, inplace=True)
        return df

    def add_cumulative_price_change(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add the cumulative price change within each tick imbalance bar.

        Purpose: Measures price movement strength and direction across the bar.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.

        """
        df.loc[:, "cumulative_price_change"] = (df["close"] - df["open"]) / df[
            "open"
        ]
        return df

    def add_high_low_pct_range(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add the high-low percentage range within each bar.

        Purpose: Captures the volatility and price range within each bar.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.

        """
        df.loc[:, "high_low_pct"] = (df["high"] - df["low"]) / df["low"]
        return df

    def add_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Volume Weighted Average Price (VWAP) within each bar.

        Purpose: Provides a benchmark for the average traded price per volume,
        indicating value.
        """
        df.loc[:, "vwap"] = (df["close"] * df["volume"]).cumsum() / df[
            "volume"
        ].cumsum()
        return df

    def add_average_trade_size(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add average trade size within each bar.

        Purpose: Identifies average transaction size, which can indicate
        institutional activity.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.

        """
        df.loc[:, "average_trade_size"] = df["volume"] / np.abs(
            df["tick_imbalance"]
        )
        return df

    def add_accumulation_distribution_index(
        self, df: pd.DataFrame
    ) -> pd.DataFrame:
        """Add Accumulation/Distribution Index (ADI).

        ADI is computed based on close, high, low, and volume.

        Purpose: Tracks the cumulative flow of volume into or out of an
        asset to identify accumulation or distribution.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.

        """
        df.loc[:, "adi"] = (
            ((df["close"] - df["low"]) - (df["high"] - df["close"]))
            * df["volume"]
            / (df["high"] - df["low"] + 1e-5)
        )
        return df

    def add_moving_average(self, df: pd.DataFrame, window: int = 10):
        """Add a simple moving average of close prices over a specified window.

        Nans are filled with a progressive rolling average.

        Purpose: Smooths short-term price fluctuations and captures
        longer-term trends.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.
        window (int): The window size for the moving average.

        """
        df.loc[:, f"moving_avg_{window}"] = (
            df["close"].rolling(window=window).mean()
        )
        for i in range(window - 1):
            df.loc[i, f"moving_avg_{window}"] = (
                df["close"].iloc[: i + 1].rolling(i + 1).mean().iloc[i]
            )
        return df

    def add_ema(self, df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """Add an Exponential Moving Average (EMA) of the close price.

        Purpose: Provides a smoother moving average that responds more
        quickly to recent prices.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.
        window (int): The window size for the moving average.

        """
        df.loc[:, f"ema_{window}"] = talib.EMA(df["close"], timeperiod=window)
        for i in range(1, window):
            df.loc[i, f"ema_{window}"] = talib.EMA(
                df["close"].iloc[: i + 1], timeperiod=i + 1
            ).iloc[-1]
        df[f"ema_{window}"].fillna(df["close"].iloc[0], inplace=True)
        return df

    def add_skewness(self, df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """Add skewness of returns within a rolling window.

        Purpose: Measures asymmetry in the distribution of returns,
        indicating directional bias.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.
        window (int): The window size for the rolling skewness calculation.

        """
        df.loc[:, "skewness"] = (
            df["log_return_1"]
            .rolling(window=window)
            .apply(lambda x: x.skew(), raw=False)
        )
        mean = df["skewness"].mean()
        for i in range(window - 1):
            df.loc[i, "skewness"] = (
                df["log_return_1"]
                .iloc[: i + 1]
                .rolling(i + 1)
                .apply(lambda x: x.skew(), raw=False)
                .iloc[i]
            )
        df["skewness"].fillna(mean, inplace=True)
        return df

    def add_kurtosis(self, df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """Add kurtosis of returns within a rolling window.

        Purpose: Measures the 'tailedness' of returns distribution, indicating
        outlier likelihood.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.
        window (int): The window size for the rolling kurtosis calculation.

        """
        df.loc[:, "kurtosis"] = (
            df["log_return_1"]
            .rolling(window=window)
            .apply(lambda x: x.kurt(), raw=False)
        )
        mean = df["kurtosis"].mean()
        for i in range(window - 1):
            df.loc[i, "kurtosis"] = (
                df["log_return_1"]
                .iloc[: i + 1]
                .rolling(i + 1)
                .apply(lambda x: x.kurt(), raw=False)
                .iloc[i]
            )
        df["kurtosis"].fillna(mean, inplace=True)
        return df

    def add_temporal_features(
        self, df: pd.DataFrame, timeperiod: int = 10
    ) -> pd.DataFrame:
        """Add temporal features based on bar end_time.

        Purpose: Capture potential temporal patterns in the data.
        E.g., hours where volatility is higher/lower.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.
        timeperiod (str): Temporal timeframe to compute temporal features on.

        """
        if timeperiod == "month day":
            df.loc[:, "month_day"] = df["end_time"].dt.day
        elif timeperiod == "week day":
            df.loc[:, "weekday"] = df["end_time"].dt.dayofweek
        elif timeperiod == "hour":
            df.loc[:, "hour"] = df["end_time"].dt.hour
        elif timeperiod == "minute":
            df.loc[:, "minute"] = df["end_time"].dt.minute
        else:
            logger.error(
                f"Temporal feature {timeperiod} not supported. "
                "Supported temp. features:  month day, week day, hour, minute"
            )
        return df

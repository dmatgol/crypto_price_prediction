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
        """Add features to the df based on the configuration dictionary."""
        df = self.df.copy()
        for feature_name, parms in self.config.items():
            method_name = f"add_{feature_name}"
            method = getattr(self, method_name, None)
            if method:
                df = method(df, **parms) if parms else method(df)
            else:
                logger.debug(f"Method {method_name} not found.")
        return df

    def add_log_return(self, df: pd.DataFrame, n_bars: int) -> pd.DataFrame:
        """Add log return feature to the dataframe.

        Purpose: Capture compounded returns over bars
        """
        df[f"log_return_{n_bars}"] = np.log(
            df["close"] / df["close"].shift(n_bars).fillna(0)
        )
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
        df[f"rsi_{rsi_timeperiod}"] = talib.RSI(
            df["close"], timeperiod=rsi_timeperiod
        )
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
        df[f"momentum_{momentum_timeperiod}"] = talib.MOM(
            df["close"], timeperiod=momentum_timeperiod
        )
        return df

    def add_volatility_indicator(
        self, df: pd.DataFrame, vol_timeperiod: int | None = 14
    ) -> pd.DataFrame:
        """Add Volatility indicator to the dataframe.

        Purpose: Measure the variability in returns, indicating risk
        and potential future movement.

        Args:
        ----
        df (pd.DataFrame): The dataframe to process.
        vol_timeperiod (int): The time period for the volatility indicator.

        """
        df[f"volatility_{vol_timeperiod}"] = (
            df["pct_change"].rolling(window=vol_timeperiod).std()
        )
        return df

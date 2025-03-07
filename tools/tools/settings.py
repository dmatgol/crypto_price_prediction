from pydantic_settings import BaseSettings, SettingsConfigDict  # isort:skip
from enum import Enum


class SupportedCoins(Enum):
    """Supported exchanges."""

    ETH_USD: str = "ETH-USD"
    BTC_USD: str = "BTC-USD"
    LTC_USD: str = "LTC-USD"
    XRP_USD: str = "XRP-USD"

    @classmethod
    def get_supported_exchanges(cls) -> list[str]:
        """Get supported exchanges."""
        return [coin.name for coin in cls]

    @classmethod
    def validate(cls, coin_name: str) -> bool:
        """Validate coin name."""
        return coin_name in cls.get_supported_exchanges()


class AppSettings(BaseSettings):
    """App settings."""

    feature_group: str
    feature_group_version: int
    feature_view: str
    feature_view_version: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )


class HopsworkSettings(BaseSettings):
    """Database settings."""

    project_name: str
    api_key: str

    model_config = SettingsConfigDict(
        env_file=".credentials.env",
        env_prefix="HOPSWORKS__",
        env_nested_delimiter="__",
        extra="ignore",
    )


class CometMLSettings(BaseSettings):
    """Database settings."""

    project_name: str
    api_key: str
    workspace: str
    model_name: str

    model_config = SettingsConfigDict(
        env_file=".credentials.env",
        env_prefix="COMET_ML__",
        env_nested_delimiter="__",
        extra="ignore",
    )


class Settings(BaseSettings):
    """Settings."""

    app_settings: AppSettings = AppSettings()
    hopswork: HopsworkSettings = HopsworkSettings()
    comet_ml: CometMLSettings = CometMLSettings()

    features_configuration: str = "src/config/features.yaml"


settings = Settings()

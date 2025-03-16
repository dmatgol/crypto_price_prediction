from pydantic_settings import BaseSettings, SettingsConfigDict  # isort:skip
from enum import Enum

from pydantic import BaseModel


class SupportedCoins(Enum):
    """Supported exchanges."""

    ETH_USD: str = "ETH-USD"
    BTC_USD: str = "BTC-USD"
    LTC_USD: str = "LTC-USD"
    XRP_USD: str = "XRP-USD"

    @classmethod
    def get_supported_coins(cls) -> list[str]:
        """Get supported exchanges."""
        return [coin.value for coin in cls]

    @classmethod
    def validate(cls, coin_name: str) -> bool:
        """Validate coin name."""
        return coin_name in cls.get_supported_coins()


class AppSettings(BaseSettings):
    """App settings."""

    feature_group: str | None = None
    feature_group_version: int | None = None
    feature_view: str
    feature_view_version: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP__",
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


class CometMLCredentials(BaseSettings):
    """CometML credentials settings."""

    api_key: str
    project_name: str
    workspace: str

    model_config = SettingsConfigDict(
        env_file=".credentials.env",
        env_prefix="COMET_ML__",
        env_nested_delimiter="__",
        extra="ignore",
    )


class CometMLGeneralConfig(BaseSettings):
    """CometML general configuration settings (non-credentials)."""

    name_model: str
    status: str
    output_folder: str = "src/"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="COMET_ML__",
        env_nested_delimiter="__",
        extra="ignore",
    )


class CometMLSettings(BaseModel):
    """Combined CometML settings with credentials and general configuration."""

    credentials: CometMLCredentials = CometMLCredentials()
    general_config: CometMLGeneralConfig = CometMLGeneralConfig()


class Settings(BaseSettings):
    """Settings."""

    app_settings: AppSettings = AppSettings()
    hopswork: HopsworkSettings = HopsworkSettings()
    comet_ml: CometMLSettings = CometMLSettings()

    features_configuration: str = "src/config/features.yaml"


settings = Settings()

from pydantic_settings import (  # isort:skip
    BaseSettings,
    SettingsConfigDict,
)


class SupportedCoins:
    """Supported exchanges."""

    ETH_USD: str = "ETH-USD"
    BTC_USD: str = "BTC-USD"
    LTC_USD: str = "LTC-USD"
    XRP_USD: str = "XRP-USD"

    @classmethod
    def get_supported_exchanges(cls) -> list[str]:
        """Get supported exchanges."""
        return [cls.ETH_USD, cls.BTC_USD, cls.LTC_USD, cls.XRP_USD]


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
        env_nested_delimiter="__",
        extra="ignore",
    )


class Settings(BaseSettings):
    """Settings."""

    app_settings: AppSettings = AppSettings()
    hopswork: HopsworkSettings = HopsworkSettings()

    supported_coins: list[str] = SupportedCoins.get_supported_exchanges()


settings = Settings()

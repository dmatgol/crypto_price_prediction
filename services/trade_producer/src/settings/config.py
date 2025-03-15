from typing import Optional

from pydantic import field_validator

from pydantic_settings import (  # isort:skip
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class HighVolumeCoinPairs:
    """Enumeration of coins with high trade volume.

    This class contains constants representing the names of the coins with
    high trade volume.
    """

    ETH: str = "ETHUSD"
    BTC: str = "BTCUSD"


class SupportedExchanges:
    """Supported exchanges."""

    COINBASE: str = "coinbase"
    KRAKEN: str = "kraken"

    @classmethod
    def get_supported_exchanges(cls) -> list[str]:
        """Get supported exchanges."""
        return [cls.COINBASE, cls.KRAKEN]


class KafkaSettings(BaseSettings):
    """Database settings."""

    kafka_broker_address: str = None
    kafka_topic: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )


class Exchange(BaseSettings):
    """Exchange settings."""

    name: str
    product_ids: list[str]
    channels: list[str]

    @field_validator("name")
    def validate_exchange_name(cls, value):
        """Validate exchange name."""
        supported_exchanges = SupportedExchanges.get_supported_exchanges()
        if value not in supported_exchanges:
            raise ValueError(
                f"Unsupported exchange: {value}. Supported exchanges"
                f"are: {supported_exchanges}"
            )
        return value


class LiveHistoricalSettings(BaseSettings):
    """Run live or historical."""

    live_or_historical: str
    last_n_days: Optional[int]
    cache_dir_historical_data: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @field_validator("live_or_historical")
    def validate_live_or_historical(cls, value):
        """Validate live_or_historical."""
        if value not in ["live", "historical"]:
            raise ValueError(
                f"Unsupported value: {value}. Supported values"
                f"are: live, historical"
            )
        return value


class Settings(BaseSettings):
    """Settings."""

    kafka: KafkaSettings = KafkaSettings()
    exchanges: list[Exchange]
    live_or_historical_settings: LiveHistoricalSettings = (
        LiveHistoricalSettings()
    )

    model_config = SettingsConfigDict(
        yaml_file="src/configs/config.yaml",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[YamlConfigSettingsSource, ...]:
        """Customise sources."""
        return (
            env_settings,
            YamlConfigSettingsSource(
                settings_cls,
            ),
        )


settings = Settings()

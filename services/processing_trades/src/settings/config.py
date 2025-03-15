from pydantic import field_validator

from pydantic_settings import (  # isort:skip
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


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

    kafka_broker_address: str | None = None
    kafka_input_topic: str
    kafka_output_topic: str
    kafka_consumer_group: str

    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__"
    )


class AggregationMethod(BaseSettings):
    """Generic class for different data aggregation strategies."""

    type: str
    interval: float  # Generic interval, can represent volume, time, or tick

    @field_validator("type")
    def validate_type(cls, value):
        """Validate if data aggregation type is supported."""
        allowed_types = {"volume", "time", "tick imbalance"}
        if value not in allowed_types:
            raise ValueError(
                f"Type '{value}' not allowed. Must be one of {allowed_types}."
            )
        return value


class ProductId(BaseSettings):
    """Product id settings."""

    coin: str
    aggregation: AggregationMethod


class Exchange(BaseSettings):
    """Exchange settings."""

    name: str
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


class Settings(BaseSettings):
    """Settings."""

    kafka: KafkaSettings = KafkaSettings()
    exchanges: list[Exchange]
    product_ids: list[ProductId]

    model_config = SettingsConfigDict(
        yaml_file="src/configs/tick_imbalance_config.yaml",
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
            YamlConfigSettingsSource(
                settings_cls,
            ),
        )


settings = Settings()

PRODUCT_ID_MAPPING: dict[str, str] = {
    "ETH-USD": "ETH-USD",
    "ETH/USD": "ETH-USD",  # Kraken specific
    "BTC-USD": "BTC-USD",
    "BTC/USD": "BTC-USD",  # Kraken specific
    "LTC-USD": "LTC-USD",
    "LTC/USD": "LTC-USD",  # Kraken specific
    "XRP-USD": "XRP-USD",
    "XRP/USD": "XRP-USD",  # Kraken specific
}

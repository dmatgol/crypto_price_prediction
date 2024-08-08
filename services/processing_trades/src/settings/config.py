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

    kafka_broker_address: str
    kafka_input_topic: str
    kafka_output_topic: str

    model_config = SettingsConfigDict(
        env_file=".env", env_nested_delimiter="__"
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


class Settings(BaseSettings):
    """Settings."""

    kafka: KafkaSettings = KafkaSettings()
    exchanges: list[Exchange]
    volume_interval: int

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
            YamlConfigSettingsSource(
                settings_cls,
            ),
        )


settings = Settings()

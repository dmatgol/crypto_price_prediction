from pydantic import field_validator

from pydantic_settings import (  # isort:skip
    BaseSettings,
    SettingsConfigDict,
)


class KafkaSettings(BaseSettings):
    """Database settings."""

    broker_address: str
    input_topic: str | None = None
    output_topic: str | None = None
    consumer_group: str
    feature_group: str
    feature_group_version: int

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
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )


class Settings(BaseSettings):
    """Settings."""

    kafka: KafkaSettings = KafkaSettings()
    hopswork: HopsworkSettings = HopsworkSettings()
    buffer_size: int = 100000
    live_or_historical: str
    save_every_n_sec: int

    model_config = SettingsConfigDict(
        env_file=".env",
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


settings = Settings()

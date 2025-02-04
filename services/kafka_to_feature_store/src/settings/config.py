from pydantic import field_validator

from pydantic_settings import (  # isort:skip
    BaseSettings,
    SettingsConfigDict,
)


class AppSettings(BaseSettings):
    """App settings."""

    kafka_broker_address: str
    input_topic: str | None = None
    output_topic: str | None = None
    consumer_group: str
    create_new_consumer_group: bool = False
    feature_group: str
    feature_group_version: int
    feature_group_primary_keys: list[str]
    feature_group_event_time: str
    buffer_size: int = 1

    model_config = SettingsConfigDict(
        env_file="services/kafka_to_feature_store/.env",
        env_nested_delimiter="__",
        extra="ignore",
    )


class HopsworkSettings(BaseSettings):
    """Database settings."""

    project_name: str
    api_key: str

    model_config = SettingsConfigDict(
        env_file="services/kafka_to_feature_store/credentials.env",
        env_nested_delimiter="__",
        extra="ignore",
    )


class Settings(BaseSettings):
    """Settings."""

    app_settings: AppSettings = AppSettings()
    hopswork: HopsworkSettings = HopsworkSettings()
    live_or_historical: str
    save_every_n_sec: int

    model_config = SettingsConfigDict(
        env_file="services/kafka_to_feature_store/.env",
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

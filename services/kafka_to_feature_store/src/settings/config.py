from pydantic_settings import (  # isort:skip
    BaseSettings,
    SettingsConfigDict,
)


class KafkaSettings(BaseSettings):
    """Database settings."""

    broker_address: str
    input_topic: str | None = None
    output_topic: str | None = None

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
        env_file="services/kafka_to_feature_store/.env",
        env_nested_delimiter="__",
        extra="ignore",
    )


class Settings(BaseSettings):
    """Settings."""

    kafka: KafkaSettings = KafkaSettings()
    hopswork: HopsworkSettings = HopsworkSettings()


settings = Settings()

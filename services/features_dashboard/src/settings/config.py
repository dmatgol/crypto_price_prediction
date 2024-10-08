from pydantic_settings import (  # isort:skip
    BaseSettings,
    SettingsConfigDict,
)


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


settings = Settings()

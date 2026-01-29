# Storage Database

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    URI: str = "sqlite:///database.db"

    model_config = SettingsConfigDict(
        env_prefix="DB",
    )


settings = Settings()

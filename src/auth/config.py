from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    JWT_KEY: SecretStr = (
        "9c3f27f36de6739e3d8a9ec2f07372c80146d66d918535c26d8d91dd8256f4c6"
    )
    JWT_ALG: str = "HS256"
    JWT_EXP: int = 30

    model_config = SettingsConfigDict(
        env_prefix="AUTH",
    )


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    DATABASE_SERVER: str
    DATABASE_NAME: str
    DATABASE_DRIVER: str

    DATABASE_USERNAME: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None
    DATABASE_TRUSTED_CONNECTION: str = "yes"
    SQL_ECHO: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()

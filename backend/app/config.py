from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cotizador de envíos"
    database_url: str = "postgresql://manuable:manuable@database:5432/manuable"
    commercial_username: str = "comercial"
    commercial_password: str = "comercial123"
    session_secret: str = "local-development-secret-change-in-production"
    session_ttl_seconds: int = 28_800
    secure_cookies: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

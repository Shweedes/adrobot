"""Настройки приложения из окружения и файла `.env`."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Параметры запуска.

    Пустой `keitaro_api_key` допустим, чтобы работали миграции;
    приложение проверяет ключ на старте.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    keitaro_base_url: str = "https://keitaro-for-tests.etolegko.com"
    keitaro_api_key: SecretStr = SecretStr("")
    keitaro_timeout: float = 15.0

    keitaro_domain: str = "kt-emulator.test"
    keitaro_group: str = "FORTESTS"
    keitaro_source: str = "FORTESTS"

    campaign_prefix: str = "test_surname_"
    edit_only_prefixed: bool = True
    redirect_url: str = "https://google.com"

    stats_timezone: str = "UTC"
    cache_ttl_seconds: int = 60
    database_url: str = "sqlite+aiosqlite:///./adrobot.db"

    @property
    def keitaro_api_url(self) -> str:
        """Базовый URL Admin API с завершающим слэшем."""
        base = self.keitaro_base_url.rstrip("/").removesuffix("/admin")
        return f"{base}/admin_api/v1/"


@lru_cache
def get_settings() -> Settings:
    """Возвращает единственный экземпляр настроек."""
    return Settings()

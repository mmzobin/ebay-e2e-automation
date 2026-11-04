"""Central configuration.

Priority (highest wins):
    1. Environment variables / .env   (e.g. HEADLESS=true, EBAY_USER=...)
    2. YAML profile config/profiles/<TEST_PROFILE>.yaml
    3. Defaults declared below
"""
from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT_DIR / "config" / "profiles"
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"

load_dotenv(ROOT_DIR / ".env")


class AuthMode(str, Enum):
    GUEST = "guest"
    CREDENTIALS = "credentials"


class Viewport(BaseModel):
    width: int = 1440
    height: int = 900


class YamlProfileSource(PydanticBaseSettingsSource):
    """Loads values from the YAML profile selected by TEST_PROFILE."""

    def __init__(self, settings_cls: type[BaseSettings]):
        super().__init__(settings_cls)
        profile = os.getenv("TEST_PROFILE", "default")
        path = PROFILES_DIR / f"{profile}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Profile '{profile}' not found: {path}")
        self._data: dict[str, Any] = yaml.safe_load(path.read_text()) or {}
        self._data["profile"] = profile

    def get_field_value(self, field, field_name):  # pragma: no cover - required by ABC
        return self._data.get(field_name), field_name, False

    def __call__(self) -> dict[str, Any]:
        return self._data


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__", extra="ignore")

    profile: str = "default"
    base_url: str = "https://www.ebay.com"
    browser: str = "chromium"
    headless: bool = True
    slow_mo: int = 0
    locale: str = "en-US"
    timezone_id: str = "America/New_York"
    viewport: Viewport = Field(default_factory=Viewport)
    default_timeout_ms: int = 15_000
    navigation_timeout_ms: int = 45_000
    max_pages: int = 5

    auth_mode: AuthMode = AuthMode.GUEST
    ebay_user: str | None = None
    ebay_password: SecretStr | None = None  # SecretStr: never printed in logs/repr

    @property
    def has_credentials(self) -> bool:
        return bool(self.ebay_user and self.ebay_password)

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings
    ):
        return init_settings, env_settings, YamlProfileSource(settings_cls)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

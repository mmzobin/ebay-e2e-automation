"""Configuration: YAML profile (config/profiles/<TEST_PROFILE>.yaml) + ENV overrides."""
import os
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"


@dataclass(frozen=True)
class Settings:
    profile: str
    base_url: str
    headless: bool
    locale: str
    default_timeout_ms: int
    max_pages: int
    ebay_user: str | None
    ebay_password: str | None

    @property
    def has_credentials(self) -> bool:
        return bool(self.ebay_user and self.ebay_password)

    def __repr__(self) -> str:  # never print the password
        return f"Settings(profile={self.profile}, base_url={self.base_url}, headless={self.headless})"


def load_settings() -> Settings:
    profile = os.getenv("TEST_PROFILE", "default")
    data = yaml.safe_load((ROOT_DIR / "config" / "profiles" / f"{profile}.yaml").read_text())
    return Settings(
        profile=profile,
        base_url=os.getenv("BASE_URL", data["base_url"]),
        headless=os.getenv("HEADLESS", str(data["headless"])).lower() == "true",
        locale=data["locale"],
        default_timeout_ms=int(data["default_timeout_ms"]),
        max_pages=int(os.getenv("MAX_PAGES", data["max_pages"])),
        ebay_user=os.getenv("EBAY_USER"),
        ebay_password=os.getenv("EBAY_PASSWORD"),
    )


settings = load_settings()

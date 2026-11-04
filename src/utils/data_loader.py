from __future__ import annotations

from pathlib import Path

import yaml

from config.settings import DATA_DIR
from src.models.search import SearchScenario


def load_search_scenarios(file_name: str = "search_scenarios.yaml") -> list[SearchScenario]:
    """Read external test data and validate it into typed models."""
    path: Path = DATA_DIR / file_name
    raw = yaml.safe_load(path.read_text()) or {}
    return [SearchScenario(**item) for item in raw.get("scenarios", [])]

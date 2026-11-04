import yaml

from config.settings import DATA_DIR
from src.models.search import SearchScenario


def load_search_scenarios(file_name: str = "search_scenarios.yaml") -> list[SearchScenario]:
    """Read external test data (data-driven input)."""
    raw = yaml.safe_load((DATA_DIR / file_name).read_text())
    return [SearchScenario(**item) for item in raw["scenarios"]]

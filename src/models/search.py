from dataclasses import dataclass


@dataclass(frozen=True)
class SearchScenario:
    """One row of data/search_scenarios.yaml."""

    id: str
    query: str
    max_price: float
    limit: int = 5

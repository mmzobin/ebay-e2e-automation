from dataclasses import dataclass


@dataclass(frozen=True)
class SearchScenario:
    """One row of data/search_scenarios.yaml."""

    id: str
    query: str
    max_price: float
    limit: int = 5


@dataclass(frozen=True)
class SearchResultItem:
    """One product card parsed from the search results page."""

    title: str
    url: str
    price: float | None

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field


class SearchScenario(BaseModel):
    """One row of data/search_scenarios.yaml."""

    id: str
    query: str = Field(min_length=1)
    max_price: float = Field(gt=0)
    limit: int = Field(default=5, gt=0)


@dataclass(frozen=True)
class SearchResultItem:
    title: str
    url: str
    price: float

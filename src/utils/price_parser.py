"""Parsing of price strings as rendered by eBay.

Examples handled:
    "$12.99"                 -> 12.99
    "US $1,234.56"           -> 1234.56
    "ILS 45.10"              -> 45.10
    "$10.00 to $25.00"       -> range 10.00 .. 25.00
    "EUR 1.234,50"           -> 1234.50
    "Free shipping" / ""     -> None
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

_NUMBER_RE = re.compile(r"\d[\d.,\s ]*")
_CURRENCY_RE = re.compile(r"(US\s?\$|C\s?\$|AU\s?\$|\$|€|£|₪|[A-Z]{3})")


class RangeStrategy(str, Enum):
    """Which value of a price range ("$10 to $25") represents the item."""

    MIN = "min"
    MAX = "max"


@dataclass(frozen=True)
class Price:
    low: float
    high: float
    currency: str | None = None

    @property
    def is_range(self) -> bool:
        return self.low != self.high

    def value(self, strategy: RangeStrategy = RangeStrategy.MAX) -> float:
        return self.high if strategy is RangeStrategy.MAX else self.low


class PriceParser:
    """Stateless parser; kept as a class so the strategy can be injected/overridden."""

    def __init__(self, range_strategy: RangeStrategy = RangeStrategy.MAX):
        # MAX by default: a variant is chosen randomly later, so the conservative
        # (highest) value guarantees the cart still fits the budget.
        self.range_strategy = range_strategy

    def parse(self, text: str | None) -> Price | None:
        if not text:
            return None
        numbers = [self._to_float(m) for m in _NUMBER_RE.findall(text)]
        numbers = [n for n in numbers if n is not None]
        if not numbers:
            return None
        currency_match = _CURRENCY_RE.search(text)
        currency = currency_match.group(1).replace(" ", "") if currency_match else None
        return Price(low=min(numbers), high=max(numbers), currency=currency)

    def parse_amount(self, text: str | None) -> float | None:
        price = self.parse(text)
        return price.value(self.range_strategy) if price else None

    @staticmethod
    def _to_float(raw: str) -> float | None:
        s = raw.strip().replace(" ", "").replace(" ", "").rstrip(".,")
        if not s:
            return None
        if "," in s and "." in s:
            # The last separator is the decimal one: "1,234.56" vs "1.234,56"
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            # "12,50" -> decimal comma; "1,234" -> thousands separator
            head, _, tail = s.rpartition(",")
            s = f"{head.replace(',', '')}.{tail}" if len(tail) == 2 else s.replace(",", "")
        try:
            return float(s)
        except ValueError:
            return None

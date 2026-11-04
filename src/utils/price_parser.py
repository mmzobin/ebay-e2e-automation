# examples: "$12.99", "US $1,234.56", "ILS 45.10", "$10.00 to $25.00"
import re

_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def parse_price(text: str | None) -> float | None:
    # for a range I take the higher price - variant is picked randomly later,
    # so the cart can't go over budget
    if not text:
        return None
    numbers = [float(n.replace(",", "")) for n in _NUMBER_RE.findall(text)]
    return max(numbers) if numbers else None

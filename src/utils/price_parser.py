"""Price string parsing: "$12.99", "US $1,234.56", "ILS 45.10", "$10.00 to $25.00"."""
import re

_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def parse_price(text: str | None) -> float | None:
    """Return the price as float, or None if the text has no number.

    For a range ("$10.00 to $25.00") the HIGHER value is returned: a variant is
    picked randomly later, so the conservative value keeps the cart within budget.
    """
    if not text:
        return None
    numbers = [float(n.replace(",", "")) for n in _NUMBER_RE.findall(text)]
    return max(numbers) if numbers else None

import pytest

from src.utils.price_parser import PriceParser, RangeStrategy

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "text, expected",
    [
        ("$12.99", 12.99),
        ("US $1,234.56", 1234.56),
        ("ILS 45.10", 45.10),
        ("EUR 1.234,50", 1234.50),
        ("£7,50", 7.50),
        ("$1,000", 1000.0),
        ("$ 99.00 ", 99.0),
        ("$10.00 to $25.00", 25.00),  # range -> MAX by default
    ],
)
def test_parse_amount(text, expected):
    assert PriceParser().parse_amount(text) == pytest.approx(expected)


@pytest.mark.parametrize("text", [None, "", "Free shipping", "See price"])
def test_unparseable_returns_none(text):
    assert PriceParser().parse_amount(text) is None


def test_range_min_strategy():
    assert PriceParser(RangeStrategy.MIN).parse_amount("$10.00 to $25.00") == 10.00


def test_range_details():
    price = PriceParser().parse("US $10.00 to US $25.00")
    assert price.is_range
    assert (price.low, price.high, price.currency) == (10.0, 25.0, "US$")

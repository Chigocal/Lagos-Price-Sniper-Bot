import pytest

from src.scraper.jumia import clean_price


@pytest.mark.parametrize(
    ("input_str", "expected"),
    [
        ("\u20a6 4,500", 4500),
        ("\u20a6 1,200,000", 1200000),
        ("\u20a6 4,500 - \u20a6 5,000", 4500),
        ("0", 0),
        ("", 0),
        ("\u20a6 0", 0),
    ],
)
def test_clean_price(input_str, expected):
    assert clean_price(input_str) == expected

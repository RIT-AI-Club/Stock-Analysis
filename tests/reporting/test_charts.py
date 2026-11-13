import pytest

from stock_analysis.reporting import ChartReference


def test_valid_chart_reference() -> None:
    chart = ChartReference("price-history_2", "Price", "Month-end close")
    assert chart.id == "price-history_2"


@pytest.mark.parametrize("chart_id", ["", "Price", "price history", "-x", 'a"b', "a<b"])
def test_rejects_malformed_ids(chart_id: str) -> None:
    with pytest.raises(ValueError, match="Invalid chart id"):
        ChartReference(chart_id, "Title", "Description")


@pytest.mark.parametrize(("title", "description"), [("", "d"), ("  ", "d"), ("t", ""), ("t", " ")])
def test_requires_title_and_description(title: str, description: str) -> None:
    with pytest.raises(ValueError, match="needs a"):
        ChartReference("x", title, description)

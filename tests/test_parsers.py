import pytest
from bs4 import BeautifulSoup
from src.scrapers.parsers import NationalPageParsingStrategy
from pathlib import Path

@pytest.fixture
def national_page_soup():
    """Loads the sample national page HTML into a BeautifulSoup object."""
    html_path = Path(__file__).parent / "fixtures" / "national_page_2020.html"
    with open(html_path, 'r', encoding='utf-8') as f:
        return BeautifulSoup(f.read(), 'html.parser')

def test_national_page_parsing_strategy_success(national_page_soup):
    """Tests the strategy with valid HTML."""
    parser = NationalPageParsingStrategy()
    data = parser.parse(national_page_soup)

    assert data is not None
    assert len(data) == 2  # Should only find Democratic and Republican

    dem_data = next(item for item in data if item["party"] == "Democratic")
    rep_data = next(item for item in data if item["party"] == "Republican")

    assert dem_data['leader'] == "Joseph R. Biden, Jr."
    assert dem_data['popular_votes'] == "81,283,501"

    assert rep_data['leader'] == "Donald J. Trump"
    assert rep_data['popular_votes'] == "74,223,975"

def test_national_page_parsing_strategy_no_table(caplog):
    """Tests behavior when the target table is missing."""
    soup = BeautifulSoup("<div><p>No table here</p></div>", "html.parser")
    parser = NationalPageParsingStrategy()
    data = parser.parse(soup)

    assert data is None
    assert "Strategy could not find 'table-responsive' div" in caplog.text
"""
Contains stateless parsing functions implemented using the Strategy Design Pattern.
Each class represents a different strategy for parsing a specific type of page.
"""
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import abc

logger = logging.getLogger(__name__)
TARGET_PARTIES = ["Democratic", "Republican"]

class ParsingStrategy(abc.ABC):
    """
    The abstract base class for a parsing strategy. This defines the
    interface that all concrete parsing strategies must implement.
    """
    @abc.abstractmethod
    def parse(self, content: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
        """The main parse method."""
        pass


class NationalPageParsingStrategy(ParsingStrategy):
    """
    A concrete implementation of a parsing strategy for the national election
    year pages on 270towin.com (e.g., /2020-election).
    """
    def parse(self, soup: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
        """
        Parses the HTML soup to extract candidate and vote data for major parties.

        Args:
            soup: A BeautifulSoup object of the page.

        Returns:
            A list of dictionaries, one for each major party candidate,
            or None if the main table is not found.
        """
        election_data = []

        table_div = soup.find('div', class_='table-responsive')
        if not table_div:
            logger.warning("Strategy could not find 'table-responsive' div.")
            return None

        results_tbody = table_div.find('tbody')
        if not results_tbody:
            logger.warning("Strategy could not find 'tbody' in results table.")
            return None

        for row in results_tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) < 6:
                continue

            try:
                party = cells[3].get_text(strip=True)
                if party in TARGET_PARTIES:
                    name = cells[2].get_text(strip=True).split('(')[0].strip()
                    election_data.append({
                        "party": party,
                        "leader": name,
                        "popular_votes": cells[5].get_text(strip=True)
                    })
                    if len(election_data) == len(TARGET_PARTIES):
                        break
            except IndexError:
                logger.warning("Skipping malformed row in national results table.")
                continue

        return election_data
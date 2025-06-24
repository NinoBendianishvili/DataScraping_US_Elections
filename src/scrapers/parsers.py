"""
Contains stateless parsing functions used by the non-Scrapy scrapers.
Currently, this is focused on parsing the national election year pages.
"""
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)
TARGET_PARTIES = ["Democratic", "Republican"]

def parse_national_election_page(soup: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
    """
    Parses the HTML soup of a national election year page (e.g., /2020-election)
    to extract candidate and vote data for the two major parties.

    Args:
        soup: A BeautifulSoup object of the page.

    Returns:
        A list of dictionaries, where each dictionary represents a candidate,
        or None if the main table is not found.
    """
    election_data = []

    # The main data is inside a div with class 'table-responsive'
    table_div = soup.find('div', class_='table-responsive')
    if not table_div:
        logger.warning("Could not find the 'table-responsive' div on the national election page.")
        return None

    results_tbody = table_div.find('tbody')
    if not results_tbody:
        logger.warning("Could not find the 'tbody' within the results table.")
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
                # Stop once we have found both major parties
                if len(election_data) == len(TARGET_PARTIES):
                    break
        except IndexError:
            logger.warning("Skipping a malformed row in the national results table.")
            continue

    return election_data
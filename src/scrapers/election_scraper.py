import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any
from .parsers import parse_national_election_page

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StateElectionScraper:
    """
    Orchestrates scraping NATIONAL election data from the site.
    State-level data is now handled by the Scrapy spider.
    """
    BASE_URL = "https://www.270towin.com"

    def __init__(self, target_years: List[int], delay_seconds: float, **kwargs):
        self.target_years = sorted(list(set(target_years)))
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
        self.national_year_data: Dict[int, Dict[str, Any]] = {}
        logging.info(f"Initialized legacy scraper for national data. Years: {self.target_years}")

    def _scrape_single_election_year(self, year: int) -> Optional[List[Dict[str, str]]]:
        """Fetches and parses a single election year page."""
        url = f"{self.BASE_URL}/{year}-election"
        logging.info(f"Attempting to scrape national data for year {year} from {url}")

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')

            # --- UPDATE: Use the dedicated parser function ---
            return parse_national_election_page(soup)

        except requests.RequestException as e:
            logging.error(f"Error fetching URL {url}: {e}")
            return None

    def _fetch_all_national_data(self):
        """Fetches national leader and vote data for all target years."""
        print(f"\nFetching national data for years: {self.target_years}...")
        for year in self.target_years:
            year_results = self._scrape_single_election_year(year)
            if year_results:
                year_entry = {}
                for candidate in year_results:
                    party_key = 'dem' if candidate['party'] == "Democratic" else 'rep'
                    year_entry[f'{party_key}_leader'] = candidate['leader']
                    year_entry[f'{party_key}_votes'] = candidate['popular_votes']
                self.national_year_data[year] = year_entry
                logging.info(f"Stored national data for {year}.")
            else:
                logging.warning(f"Could not fetch national data for {year}. Fields will be None.")
                self.national_year_data[year] = {}
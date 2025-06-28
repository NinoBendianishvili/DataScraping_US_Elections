import requests
import logging
import time
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any
from .parsers import ParsingStrategy
from ..utils.decorators import retry_on_failure # Import the new decorator

logger = logging.getLogger(__name__)

class StateElectionScraper:
    """
    Orchestrates scraping NATIONAL election data using a robust retry decorator.
    """
    BASE_URL = "https://www.270towin.com"

    def __init__(self, target_years: List[int], delay_seconds: float,
                 parsing_strategy: ParsingStrategy, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.target_years = sorted(list(set(target_years)))
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
        self.parsing_strategy = parsing_strategy
        self.national_year_data: Dict[int, Dict[str, Any]] = {}
        self.logger.info(f"Initialized legacy scraper with strategy: {parsing_strategy.__class__.__name__}")

    # --- THE DECORATOR IS APPLIED HERE ---
    # The complex retry loop is now abstracted away into the decorator.
    @retry_on_failure(max_retries=3, backoff_factor=1.5)
    def _scrape_single_election_year(self, year: int) -> Optional[List[Dict[str, str]]]:
        """
        Fetches and parses a single election year page. The retry logic
        is handled by the @retry_on_failure decorator.
        """
        url = f"{self.BASE_URL}/{year}-election"
        self.logger.info(f"Attempting to scrape national data for year {year} from {url}")

        # The core logic is now much simpler. It only runs if the request succeeds.
        response = self.session.get(url, timeout=15)

        # Handle specific HTTP errors that are not network exceptions
        if response.status_code == 429:
            self.logger.warning(f"Status 429 (Too Many Requests) for {url}. Consider increasing delay.")
            # We treat this as a failure so the decorator can back off.
            response.raise_for_status()

        response.raise_for_status()  # Raise an exception for other 4xx/5xx errors

        soup = BeautifulSoup(response.content, 'lxml')
        return self.parsing_strategy.parse(soup)

    def _fetch_all_national_data(self):
        """Fetches national leader and vote data for all target years."""
        print(f"\nFetching national data for years: {self.target_years}...")
        for i, year in enumerate(self.target_years):
            if i > 0:
                time.sleep(self.delay_seconds)

            # The call to the decorated function remains the same.
            year_results = self._scrape_single_election_year(year)

            if year_results:
                year_entry = {}
                for candidate in year_results:
                    party_key = 'dem' if candidate['party'] == "Democratic" else 'rep'
                    year_entry[f'{party_key}_leader'] = candidate['leader']
                    year_entry[f'{party_key}_votes'] = candidate['popular_votes']
                self.national_year_data[year] = year_entry
            else:
                self.logger.warning(f"Could not fetch national data for {year}. Fields will be None.")
                self.national_year_data[year] = {}
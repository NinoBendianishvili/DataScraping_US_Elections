import requests
import logging
import time
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
        self.max_retries = 3
        self.backoff_factor = 1.0  # Base delay for backoff in seconds
        logging.info(f"Initialized legacy scraper for national data. Years: {self.target_years}")

    def _scrape_single_election_year(self, year: int) -> Optional[List[Dict[str, str]]]:
        """Fetches and parses a single election year page with retries and backoff."""
        url = f"{self.BASE_URL}/{year}-election"
        logging.info(f"Attempting to scrape national data for year {year} from {url}")

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=15)

                if response.status_code == 429:
                    # Handle "Too Many Requests"
                    retry_after = int(response.headers.get("Retry-After", 0))
                    wait_time = retry_after if retry_after > 0 else self.backoff_factor * (2 ** attempt)
                    logging.warning(
                        f"Status 429 on attempt {attempt + 1}/{self.max_retries} for {url}. "
                        f"Retrying in {wait_time:.2f}s..."
                    )
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()  # Raise exception for other 4xx/5xx errors

                # If successful (2xx status code)
                soup = BeautifulSoup(response.content, 'lxml')
                return parse_national_election_page(soup)

            except requests.RequestException as e:
                logging.warning(f"Request for {url} failed on attempt {attempt + 1}/{self.max_retries}: {e}")
                if attempt + 1 == self.max_retries:
                    logging.error(f"All {self.max_retries} retries failed for {url}. Aborting scrape for this year.")
                    return None

                # Exponential backoff for other request-related errors (e.g., DNS, connection timeout)
                wait_time = self.backoff_factor * (2 ** attempt)
                logging.info(f"Waiting {wait_time:.2f}s before next retry...")
                time.sleep(wait_time)

        return None # This line is reached if all retries fail


    def _fetch_all_national_data(self):
        """Fetches national leader and vote data for all target years."""
        print(f"\nFetching national data for years: {self.target_years}...")
        for i, year in enumerate(self.target_years):
            # Add a polite delay between requests to different pages. No delay before the first one.
            if i > 0:
                time.sleep(self.delay_seconds)

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
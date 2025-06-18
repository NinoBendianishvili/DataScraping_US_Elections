import requests
import time
import logging
from bs4 import BeautifulSoup
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .parsers import (fetch_and_parse, parse_state_links,
                      parse_state_details, parse_election_results_table)
from ..data.models import StateData, YearData, ElectionResult

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StateElectionScraper:
    """
    Orchestrates scraping state pages and national year pages,
    uses parser functions, and populates data model objects.
    """
    BASE_URL = "https://www.270towin.com"
    STATES_LIST_URL = f"{BASE_URL}/states/"
    
    def __init__(self, target_years: List[int], delay_seconds: float, max_workers: int):
        self.target_years = sorted(list(set(target_years)))
        self.delay_seconds = delay_seconds
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
        self.national_year_data: Dict[int, Dict[str, Any]] = {}
        logging.info(f"Initialized scraper for years: {self.target_years} with delay {self.delay_seconds}s.")

    def _scrape_single_election_year(self, year: int) -> Optional[List[Dict[str, str]]]:
        """
        Fetches and parses election results for a specific year.
        (Logic integrated from the original years.py file)
        """
        url = f"https://www.270towin.com/{year}-election"
        logging.info(f"Attempting to scrape national data for year {year} from {url}")
        election_data = []
        found_parties_count = 0
        target_parties = ["Democratic", "Republican"]

        try:
            response = requests.get(url, headers=self.session.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            table_div = soup.find('div', class_='table-responsive')
            results_tbody = table_div.find('tbody') if table_div else None

            if not results_tbody:
                logging.warning(f"Could not find the results table body for year {year}.")
                return None

            for row in results_tbody.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) < 6: continue
                
                party = cells[3].get_text(strip=True)
                if party in target_parties:
                    name = cells[2].get_text(strip=True).split('(')[0].strip()
                    election_data.append({
                        "party": party,
                        "leader": name,
                        "popular_votes": cells[5].get_text(strip=True)
                    })
                    found_parties_count += 1
                    if found_parties_count == len(target_parties): break
            
            return election_data
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

    def get_state_links_and_names(self) -> Dict[str, str]:
        """ Fetches and parses main states page for state names and URLs. """
        print(f"\nFetching state list from {self.STATES_LIST_URL}...")
        soup = fetch_and_parse(self.STATES_LIST_URL, self.session, self.delay_seconds)
        state_links = parse_state_links(soup) if soup else {}
        print(f"Found {len(state_links)} state links.")
        return state_links

    def scrape_single_state(self, state_name: str, state_url_path: str) -> List[ElectionResult]:
        """Scrapes data for one state and returns a list of ElectionResult objects."""
        full_url = self.BASE_URL + state_url_path
        logging.info(f"Scraping {state_name} from {full_url}...")
        results_for_state = []

        soup = fetch_and_parse(full_url, self.session, self.delay_seconds)
        if not soup:
            logging.warning(f"Could not fetch or parse page for {state_name}. Skipping.")
            return results_for_state

        state_details = parse_state_details(soup)
        
        try:
            state_obj = StateData(state_name=state_name, **state_details)
            parsed_yearly_data = parse_election_results_table(soup, self.target_years)
            
            year_obj_cache = {}
            for year_data in parsed_yearly_data:
                year = year_data.get('year')
                if not year: continue
                
                national_data = self.national_year_data.get(year, {})
                
                if year not in year_obj_cache:
                    year_obj_cache[year] = YearData(year=year, **national_data)
                
                results_for_state.append(ElectionResult(
                    state_info=state_obj,
                    year_info=year_obj_cache[year],
                    dem_percentage=year_data.get('dem_pct'),
                    rep_percentage=year_data.get('rep_pct'),
                    winner=year_data.get('winner')
                ))

        except (ValueError, TypeError) as e:
            logging.error(f"Error creating data models for {state_name}: {e}. Skipping state.")
        
        return results_for_state

    def scrape_all_states(self) -> List[ElectionResult]:
        """ Orchestrates scraping all states concurrently."""
        self._fetch_all_national_data()
        
        all_results = []
        state_links = self.get_state_links_and_names()
        if not state_links: return all_results

        print(f"\nStarting concurrent scraping for {len(state_links)} states (max_workers={self.max_workers})...")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_state = {
                executor.submit(self.scrape_single_state, name, path): name
                for name, path in state_links.items()
            }
            for future in as_completed(future_to_state):
                state_name = future_to_state[future]
                try:
                    state_results = future.result()
                    if state_results:
                        all_results.extend(state_results)
                        logging.info(f"Finished {state_name}. Added {len(state_results)} results.")
                except Exception as e:
                    logging.error(f"Error processing {state_name}: {e}", exc_info=True)

        print(f"\nScraping finished. Collected {len(all_results)} total election results.")
        return all_results
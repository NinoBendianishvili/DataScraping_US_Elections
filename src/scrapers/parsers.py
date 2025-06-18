"""
Contains stateless parsing functions that use BeautifulSoup to extract
structured data from fetched HTML content.
"""
import re
import time
import requests
import logging
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Any

from ..data.models import Party

logger = logging.getLogger(__name__)

def fetch_and_parse(url: str, session: requests.Session, delay_seconds: float) -> Optional[BeautifulSoup]:
    """Fetches a URL and parses it into a BeautifulSoup object with error handling."""
    time.sleep(delay_seconds)
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing content from {url}: {e}")
        return None

def parse_state_links(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Parses the main states list page to find state names and their relative URLs.
    This version is updated to handle the current website structure.
    """
    state_links = {}
    if not soup:
        logger.warning("No soup object provided to parse_state_links.")
        return state_links

    # NEW, MORE ROBUST STRATEGY: Target the specific container div by its ID.
    # This is much more reliable than searching for generic tags like <h2>.
    container = soup.find('div', id='states_container')

    if not container:
        logger.error("Could not find the main state link container (<div id='states_container'>). The website structure has likely changed again.")
        return state_links

    # Select all anchor tags within the container that link to a state page.
    links = container.select('a[href^="/states/"]')

    for link in links:
        href = link.get('href')
        # The text inside the link is the state name.
        name = link.get_text(strip=True)

        # A final check to ensure we have a valid name and href.
        if href and name:
            # We don't need to clean the name anymore, as the " (X EV)" part is gone.
            state_links[name] = href

    # The log message is now inside the function, making it more accurate.
    logger.info(f"Extracted {len(state_links)} state links.")
    return state_links

def parse_state_details(soup: BeautifulSoup) -> Dict[str, Optional[int]]:
    """Parses a state detail page for electoral votes."""
    details = {'electoral_votes': None}
    if not soup: return details

    try:
        # Strategy 1: Find the large 'ev' span
        ev_span = soup.find('span', class_='ev')
        if ev_span and ev_span.get_text(strip=True).isdigit():
            details['electoral_votes'] = int(ev_span.get_text(strip=True))
            return details
        
        # Strategy 2: Find heading like "9 ELECTORAL VOTES"
        ev_heading = soup.find(['h2', 'h3'], string=re.compile(r'\d+\s+ELECTORAL VOTES', re.I))
        if ev_heading:
            match = re.search(r'(\d+)', ev_heading.get_text())
            if match:
                details['electoral_votes'] = int(match.group(1))
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Could not extract electoral votes: {e}")

    return details

def _parse_percentage(text: str) -> Optional[float]:
    """Helper to robustly parse percentage strings into floats."""
    if not text: return None
    match = re.search(r'([\d.]+)', text)
    if match:
        try:
            value = float(match.group(1))
            return round(value, 2) if 0 <= value <= 100.1 else None
        except ValueError:
            return None
    return None

def parse_election_results_table(soup: BeautifulSoup, target_years: List[int]) -> List[Dict[str, Any]]:
    """Parses the historical results table on a state page."""
    parsed_results = []
    if not soup: return parsed_results

    results_table = soup.find('table', id='recent_elections')
    if not results_table:
        logger.warning("Results table with id 'recent_elections' not found.")
        return parsed_results

    for row in results_table.find_all('tr', class_='toggle-row'):
        cells = row.find_all('td', recursive=False)
        if len(cells) < 2: continue

        try:
            year_text = cells[0].get_text(strip=True)
            year_match = re.search(r'(\d{4})', year_text)
            if not (year_match and int(year_match.group(1)) in target_years):
                continue
            
            year = int(year_match.group(1))
            results_cell = cells[1]
            
            # Find percentages within the results cell
            nested_cells = results_cell.select('table td')
            if len(nested_cells) >= 3:
                dem_pct = _parse_percentage(nested_cells[0].get_text())
                rep_pct = _parse_percentage(nested_cells[2].get_text())
            else:
                dem_pct, rep_pct = None, None

            winner = None
            if dem_pct is not None and rep_pct is not None:
                if dem_pct > rep_pct: winner = Party.DEMOCRATIC
                elif rep_pct > dem_pct: winner = Party.REPUBLICAN
                else: winner = Party.OTHER
            
            parsed_results.append({
                'year': year,
                'dem_pct': dem_pct,
                'rep_pct': rep_pct,
                'winner': winner
            })
        except Exception as e:
            logger.warning(f"Error parsing a result row: {e} | Row: {row.get_text('|')}")

    return parsed_results
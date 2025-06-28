import logging
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class WikipediaPopulationScraper:
    """
    Scrapes historical US state population data from a Wikipedia table.
    URL: https://en.wikipedia.org/wiki/List_of_U.S._states_and_territories_by_historical_population
    """

    URL = "https://en.wikipedia.org/wiki/List_of_U.S._states_and_territories_by_historical_population"

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = self._initialize_driver()

    def _initialize_driver(self) -> webdriver.Chrome:
        logger.info("Initializing Selenium WebDriver for Wikipedia...")
        options = ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("WebDriver initialized.")
        return driver

    def _clean_population_string(self, pop_str: str) -> Optional[int]:
        if not pop_str or not isinstance(pop_str, str):
            return None
        try:
            return int(pop_str.replace(",", "").strip())
        except (ValueError, TypeError):
            return None

    def scrape(self, target_years: List[int]) -> Optional[List[Dict]]:
        try:
            logger.info(f"Navigating to {self.URL}...")
            self.driver.get(self.URL)
            self.driver.implicitly_wait(0.5)

            tables = self.driver.find_elements(By.CSS_SELECTOR, "#mw-content-text table")
            target_table = None

            for table in tables:
                header_elements = table.find_elements(By.TAG_NAME, "th")
                headers = [th.text.strip() for th in header_elements]

                if any(str(year) in header for year in target_years for header in headers):
                    target_table = table
                    break

            if not target_table:
                logger.error("Could not find a table with the target years.")
                return None

            logger.info("Found the correct table. Parsing headers and rows...")

            header_elements = target_table.find_elements(By.TAG_NAME, "th")
            headers = [th.text.strip() for th in header_elements]

            year_to_index_map = {}
            for year in target_years:
                year_str = str(year)
                for i, header in enumerate(headers):
                    if header.startswith(year_str):
                        year_to_index_map[year_str] = i
                        break

            if not year_to_index_map:
                logger.error(f"Could not map any target years {target_years} to table columns. Headers found: {headers}")
                return None

            logger.info(f"Mapped column indices for years: {year_to_index_map}")

            population_data = []
            rows = target_table.find_elements(By.CSS_SELECTOR, "tbody tr")

            for row in rows[1:]:
                state_name_elements = row.find_elements(By.TAG_NAME, "th")
                if not state_name_elements:
                    continue

                state_name = state_name_elements[0].text.strip()
                cols = row.find_elements(By.TAG_NAME, "td")

                for year_str, header_index in year_to_index_map.items():
                    col_index = header_index - 1

                    if col_index < len(cols):
                        pop_str = cols[col_index].text
                        population = self._clean_population_string(pop_str)
                        if state_name and population:
                            population_data.append({
                                'state_name': state_name,
                                'year': int(year_str),
                                'population': population
                            })

            logger.info(f"Successfully scraped population data for {len(population_data)} state-year combinations.")
            return population_data

        except Exception as e:
            logger.error(f"An error occurred during Selenium scraping of Wikipedia: {e}", exc_info=True)
            return None
        finally:
            if self.driver:
                logger.info("Closing Selenium WebDriver.")
                self.driver.quit()
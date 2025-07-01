import logging
import time
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Use the centrally configured logger
logger = logging.getLogger(__name__)

class FECScraper:
    """
    Scrapes presidential candidate finance data from FEC.gov for given election years using Selenium.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = self._initialize_driver()

    def _initialize_driver(self) -> Optional[webdriver.Chrome]:
        options = ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )

        try:
            service = ChromeService(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            logger.error(f"WebDriver initialization failed: {e}", exc_info=True)
            return None

    def _clean_currency(self, value: str) -> Optional[float]:
        try:
            return float(value.replace("$", "").replace(",", "").strip())
        except Exception:
            return None

    def _scrape_current_page(self, wait: WebDriverWait) -> List[Dict]:
        """Scrapes all rows from the current table page."""
        try:
            table = wait.until(EC.visibility_of_element_located((By.ID, "DataTables_Table_0")))
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        except Exception as e:
            logger.error(f"Error locating table or rows: {e}")
            return []

        data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 3:
                continue
            name = cols[0].text.split('(')[0].strip()
            party = cols[1].text.strip()
            receipts = self._clean_currency(cols[2].text)

            if name and receipts is not None:
                data.append({
                    "candidate_name": name,
                    "party": party,
                    "total_receipts": receipts,
                })
        return data

    def _scrape_paginated_year(self, year: int, wait: WebDriverWait) -> List[Dict]:
        """Handles pagination for one year's table data."""
        results = []
        page = 1

        while True:
            logger.info(f"Scraping year {year}, page {page}...")
            try:
                overlay = (By.CSS_SELECTOR, '.overlay.is-loading')
                wait.until(EC.invisibility_of_element_located(overlay))

                table_element = self.driver.find_element(By.ID, "DataTables_Table_0")
                rows = self._scrape_current_page(wait)
                for entry in rows:
                    entry["election_year"] = year
                results.extend(rows)

                next_button = self.driver.find_element(By.ID, "DataTables_Table_0_next")
                if "disabled" in next_button.get_attribute("class"):
                    break

                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                next_button.click()
                wait.until(EC.staleness_of(table_element))
                page += 1

            except Exception as e:
                logger.warning(f"Pagination stopped early for year {year}: {e}")
                break

        return results

    def scrape(self, target_years: List[int]) -> List[Dict]:
        if not self.driver:
            logger.error("WebDriver not initialized.")
            return []

        all_data = []

        for year in target_years:
            url = f"https://www.fec.gov/data/elections/president/{year}/"
            logger.info(f"Navigating to {url}...")
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 30)

            # Wait for dropdown to be populated
            try:
                dropdown = wait.until(EC.presence_of_element_located((By.ID, "summary-cycle")))
                Select(dropdown).select_by_value(str(year))
                logger.info(f"Selected year: {year}")
            except Exception as e:
                logger.warning(f"Year selection failed for {year}: {e}")
                continue

            # Scrape paginated results
            yearly_data = self._scrape_paginated_year(year, wait)
            all_data.extend(yearly_data)

        self.driver.quit()
        logger.info(f"Scraping completed. {len(all_data)} records found.")
        return all_data

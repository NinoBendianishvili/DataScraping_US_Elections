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

logger = logging.getLogger(__name__)

class FECScraper:
    """
    Scrapes presidential candidate finance data from the specific
    '#candidate-financial-totals' table on FEC.gov.
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
        except (ValueError, TypeError):
            return None

    def _scrape_current_page(self, wait: WebDriverWait) -> List[Dict]:
        """Scrapes all rows from the currently visible candidate financial totals table."""
        try:
            # Use a more specific selector to ensure we get the right table
            table_selector = (By.CSS_SELECTOR, "#candidate-financial-totals table.dataTable")
            table = wait.until(EC.visibility_of_element_located(table_selector))
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        except Exception as e:
            logger.error(f"Error locating candidate financial table or its rows: {e}")
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
                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.overlay.is-loading')))

                # Use the more specific table selector here as well
                table_element = self.driver.find_element(By.CSS_SELECTOR, "#candidate-financial-totals table.dataTable")

                rows = self._scrape_current_page(wait)
                for entry in rows:
                    entry["election_year"] = year
                results.extend(rows)

                # Use a more specific selector for the next button to avoid ambiguity
                next_button = self.driver.find_element(By.CSS_SELECTOR, "#candidate-financial-totals #DataTables_Table_0_next")

                if "disabled" in next_button.get_attribute("class"):
                    logger.info("Last page reached for candidate totals.")
                    break

                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(0.3) # Give a moment for any potential blocking elements
                next_button.click()
                wait.until(EC.staleness_of(table_element))
                page += 1

            except Exception as e:
                logger.warning(f"Pagination stopped for year {year}: {e}")
                break
        return results

    def scrape(self, target_years: List[int]) -> List[Dict]:
        if not self.driver:
            logger.error("WebDriver not initialized.")
            return []

        all_data = []
        url = f"https://www.fec.gov/data/elections/president/{target_years[0]}/" # Go to first target year page

        try:
            logger.info(f"Navigating to base URL: {url}...")
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 30)

            # --- HANDLE COOKIE BANNER ---
            try:
                cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept']")))
                cookie_button.click()
                logger.info("Cookie banner accepted.")
            except TimeoutException:
                logger.info("Cookie banner not found, continuing.")

            for year in target_years:
                logger.info(f"--- Processing Year: {year} ---")
                try:
                    dropdown = wait.until(EC.presence_of_element_located((By.ID, "summary-cycle")))
                    Select(dropdown).select_by_value(str(year))
                    logger.info(f"Selected year: {year}")

                    # Wait for the loading overlay to appear and then disappear after selection
                    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.overlay.is-loading')))
                    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.overlay.is-loading')))

                except Exception as e:
                    logger.warning(f"Year selection failed for {year}: {e}")
                    continue

                yearly_data = self._scrape_paginated_year(year, wait)
                all_data.extend(yearly_data)

        except Exception as e:
            logger.error(f"A critical error occurred during scraping: {e}", exc_info=True)
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Scraping completed. WebDriver closed.")

        logger.info(f"Total records found: {len(all_data)}")
        return all_data
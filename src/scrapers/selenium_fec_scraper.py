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
    Scrapes presidential candidate finance data by navigating directly to each
    year's URL, with a fallback to using the dropdown menu. This version
    conditionally waits for loading overlays to handle different page behaviors.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = self._initialize_driver()

    def _initialize_driver(self) -> Optional[webdriver.Chrome]:
        options = ChromeOptions()
        if self.headless: options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
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
        data = []
        try:
            table_selector = (By.CSS_SELECTOR, "#candidate-financial-totals table.dataTable")
            table = wait.until(EC.visibility_of_element_located(table_selector))
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 3: continue
                name = cols[0].text.split('(')[0].strip()
                party = cols[1].text.strip()
                receipts = self._clean_currency(cols[2].text)
                if name and receipts is not None:
                    data.append({"candidate_name": name, "party": party, "total_receipts": receipts})
        except Exception as e:
            logger.error(f"Error locating or parsing rows on current page: {e}")
        return data

    def _scrape_paginated_year(self, wait: WebDriverWait) -> List[Dict]:
        results = []
        page = 1
        try:
            wait.until(EC.visibility_of_element_located((By.ID, "candidate-financial-totals")))
        except TimeoutException:
            logger.warning("Candidate financial totals section not found. Skipping pagination.")
            return []

        while True:
            try:
                # Conditionally wait for the loading overlay to disappear
                self._wait_for_overlay(wait)

                table_element = self.driver.find_element(By.CSS_SELECTOR, "#candidate-financial-totals table.dataTable")
                rows = self._scrape_current_page(wait)
                results.extend(rows)

                next_button = self.driver.find_element(By.CSS_SELECTOR, "#candidate-financial-totals #DataTables_Table_0_next")
                if "disabled" in next_button.get_attribute("class"):
                    break

                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(0.3)
                next_button.click()
                wait.until(EC.staleness_of(table_element))
                page += 1
            except Exception:
                logger.info(f"Pagination concluded on page {page}.")
                break
        return results

    def _wait_for_overlay(self, wait: WebDriverWait):
        """
        Conditionally waits for the loading overlay. If the overlay doesn't appear
        within a short timeout, it assumes there is no overlay and continues.
        """
        try:
            # Wait for a very short time to see if the overlay appears
            overlay = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.overlay.is-loading'))
            )
            # If it appears, wait for it to disappear
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.overlay.is-loading')))
        except TimeoutException:
            # If it doesn't appear after the short wait, that's fine. Just continue.
            pass


    def scrape(self, target_years: List[int]) -> List[Dict]:
        if not self.driver:
            logger.error("WebDriver not initialized.")
            return []

        all_data = []
        base_url = "https://www.fec.gov/data/elections/president/2024/"

        try:
            logger.info(f"Navigating to base URL to handle cookies: {base_url}")
            self.driver.get(base_url)
            wait = WebDriverWait(self.driver, 20)
            try:
                cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept']")))
                cookie_button.click()
                logger.info("Cookie banner accepted.")
            except TimeoutException:
                logger.info("Cookie banner not found, continuing.")

            for year in sorted(target_years, reverse=True):
                logger.info(f"--- Processing Year: {year} ---")
                yearly_data = []

                # STRATEGY 1: Direct Navigation
                try:
                    year_url = f"https://www.fec.gov/data/elections/president/{year}/"
                    logger.info(f"Attempting direct navigation to: {year_url}")
                    self.driver.get(year_url)
                    self._wait_for_overlay(wait) # Wait for potential overlay on direct load
                    yearly_data = self._scrape_paginated_year(wait)
                except Exception as e:
                    logger.warning(f"Direct navigation failed for {year}: {e}. Attempting fallback.")
                    yearly_data = []

                # STRATEGY 2: Fallback to Dropdown
                if not yearly_data:
                    logger.info(f"Fallback: Using dropdown for year {year}.")
                    try:
                        self.driver.get(base_url)
                        self._wait_for_overlay(wait)

                        dropdown = wait.until(EC.presence_of_element_located((By.ID, "summary-cycle")))
                        Select(dropdown).select_by_value(str(year))

                        self._wait_for_overlay(wait) # Wait for overlay after dropdown selection

                        yearly_data = self._scrape_paginated_year(wait)
                    except Exception as e:
                        logger.error(f"Fallback strategy also failed for {year}: {e}", exc_info=True)
                        continue

                for entry in yearly_data:
                    entry["election_year"] = year
                all_data.extend(yearly_data)
                logger.info(f"Successfully scraped {len(yearly_data)} records for {year}.")

        except Exception as e:
            logger.error(f"A critical, unrecoverable error occurred during scraping: {e}", exc_info=True)
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Scraping completed. WebDriver closed.")

        logger.info(f"Total FEC records found across all years: {len(all_data)}")
        return all_data
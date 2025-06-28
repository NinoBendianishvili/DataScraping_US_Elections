import logging
from typing import List, Dict, Optional
import pandas as pd
import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class TurnoutScraper:
    """
    Scrapes detailed state-level voter turnout and population statistics from
    the U.S. Elections Project by extracting data from a nested iframe.
    """
    BASE_URL = "https://www.electproject.org/{year}g"

    def __init__(self, headless: bool = True, **kwargs):
        self.headless = headless
        self.driver = None

    def _initialize_driver(self) -> Optional[webdriver.Chrome]:
        """Sets up the Selenium WebDriver."""
        try:
            options = ChromeOptions()
            if self.headless:
                options.add_argument("--headless")
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--log-level=3")
            service = ChromeService(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            logger.error(f"WebDriver initialization failed: {e}", exc_info=True)
            return None

    def _get_iframe_url_with_selenium(self, page_url: str) -> Optional[str]:
        """Finds the innermost iframe src URL for voter data."""
        try:
            self.driver.get(page_url)
            wait = WebDriverWait(self.driver, 20)
            outer_iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe")))
            self.driver.switch_to.frame(outer_iframe)
            inner_iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe")))
            iframe_url = inner_iframe.get_attribute('src')

            if iframe_url:
                logger.info(f"Nested iframe URL extracted.")
                return iframe_url
            else:
                logger.warning("Inner iframe found but no src attribute.")
                return None
        except TimeoutException:
            logger.error(f"Timed out waiting for nested iframe at {page_url}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while getting nested iframe: {e}", exc_info=True)
            return None
        finally:
            if self.driver:
                self.driver.switch_to.default_content()

    def _clean_dataframe(self, df: pd.DataFrame, year: int) -> List[Dict]:
        """
        Manually reconstructs the header from the first two rows to handle
        rowspans and messy data, then extracts the required columns.
        """
        # 1. Get the first two rows which contain the header info.
        header_row1 = df.iloc[0].fillna(method='ffill')
        header_row2 = df.iloc[1]

        # 2. Combine them into a single, clean header list.
        new_columns = []
        for i in range(len(header_row2)):
            if i == 0:
                new_columns.append(str(header_row1[i]))
                continue
            h1 = str(header_row1[i]) if pd.notna(header_row1[i]) else ''
            h2 = str(header_row2[i]) if pd.notna(header_row2[i]) else ''
            full_header = f"{h1} {h2}".strip()
            new_columns.append(full_header)

        # 3. Assign the new headers and drop the old header rows from the data.
        df.columns = new_columns
        df = df.iloc[2:].reset_index(drop=True)

        # 4. Define the mapping and find the columns using the new, clean headers.
        COLUMN_MAP = {
            'state': 'State',
            'voting_eligible_population': 'Voting-Eligible Population (VEP)',
            'voting_age_population': 'Voting-Age Population (VAP)',
            'prison': 'Prison',
            'probation': 'Probation',
            'parole': 'Parole',
            'total_ineligible_felon': 'Total Ineligible Felon',
            'overseas_eligible': 'Overseas Eligible',
        }

        found_columns = {}
        # --- THIS IS THE FIX ---
        # We iterate through our clean `new_columns` list, not the DataFrame's integer index.
        for clean_name, keyword in COLUMN_MAP.items():
            found_col = next((col for col in new_columns if keyword in col), None)
            if found_col:
                found_columns[clean_name] = found_col
            else:
                logger.warning(f"Could not find column for keyword '{keyword}' in year {year}.")

        if 'state' not in found_columns:
            logger.error(f"Critical error: 'State' column not found for year {year}. Cannot process.")
            return []

        # 5. Build the final DataFrame.
        df_clean = pd.DataFrame()
        for clean_name, raw_col_name in found_columns.items():
            df_clean[clean_name] = df[raw_col_name]

        numeric_cols = [col for col in df_clean.columns if col != 'state']
        for col in numeric_cols:
            df_clean[col] = pd.to_numeric(df_clean[col].astype(str).str.replace(',', ''), errors='coerce')

        df_clean.dropna(subset=['state'], inplace=True)
        df_clean = df_clean[~df_clean['state'].str.contains("Total|Note|United States", case=False, na=False)]
        df_clean['year'] = year

        return df_clean.where(pd.notna(df_clean), None).to_dict('records')


    def scrape(self, target_years: List[int]) -> Optional[List[Dict]]:
        """Main scraping method for all target years."""
        self.driver = self._initialize_driver()
        if not self.driver:
            return None

        all_turnout_data = []
        try:
            for year in target_years:
                logger.info(f"Scraping turnout statistics for {year}...")
                page_url = self.BASE_URL.format(year=year)
                iframe_url = self._get_iframe_url_with_selenium(page_url)

                if not iframe_url:
                    logger.warning(f"Could not get iframe URL for {year}. Skipping.")
                    continue

                try:
                    tables = pd.read_html(iframe_url, header=None) # Read with no header
                    if not tables:
                        logger.warning(f"Pandas found no tables at {iframe_url} for year {year}.")
                        continue

                    df_raw = tables[0]
                    year_data = self._clean_dataframe(df_raw, year)
                    all_turnout_data.extend(year_data)
                    logger.info(f"Successfully processed {len(year_data)} records for {year}.")

                except Exception as e:
                    logger.error(f"Failed to process table from {iframe_url} for year {year}: {e}", exc_info=True)
                    continue
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Selenium WebDriver has been closed.")

        return all_turnout_data
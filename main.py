import time
import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.settings import Settings

from src.scrapers.election_scraper import StateElectionScraper
from src.data.database import get_db_connection, create_tables, save_national_data_to_db
from src.analysis.reporter import generate_analysis_reports
from src.utils.config_loader import load_config
from src.scrapers.scrapy_crawler.election_crawler.spiders.state_spider import StateSpider

from src.scrapers.selenium_wikipedia_population import WikipediaPopulationScraper
from src.data.database import get_db_connection, create_tables, save_national_data_to_db, save_population_data_to_db

def run_legacy_scraper_for_national_data(config):
    """Runs the original scraper to fetch ONLY national data."""
    print("--- Running Legacy Scraper for National Data ---")
    scraper = StateElectionScraper(
        target_years=config['target_years'],
        delay_seconds=config['delay_seconds'],
        max_workers=config['max_workers']
    )
    scraper._fetch_all_national_data()
    return scraper.national_year_data

def run_scrapy_crawler():
    """Configures and runs the Scrapy crawler without changing directory."""
    print("--- Running Scrapy Crawler for State Data ---")

    # --- THIS IS THE NEW, ROBUST WAY ---
    # 1. Point to the Scrapy settings file
    project_settings = get_project_settings()
    settings = Settings()
    # Scrapy uses its own module loading system, so we need to tell it where to find our project
    # This is done by adding the path to the src directory to sys.path
    # The 'election_crawler' module will then be discoverable.
    sys.path.insert(0, os.path.join(os.getcwd(), 'src', 'scrapers', 'scrapy_crawler'))
    settings.setmodule('election_crawler.settings', priority='project')

    # 2. Create the process with these settings
    process = CrawlerProcess(settings)

    # 3. Crawl
    process.crawl(StateSpider)
    process.start() # The script will block here until the crawling is finished

    # 4. Clean up the path
    sys.path.pop(0)

def main():
    """Main function to run the entire scraping and analysis pipeline."""
    # This ensures all paths are relative to the project root where main.py is run
    project_root = os.getcwd()

    config = load_config()
    if config is None:
        print("Configuration could not be loaded. Aborting execution.")
        sys.exit(1)

    conn = get_db_connection()
    create_tables(conn)
    conn.close()

    print("=" * 30)
    print("Starting Election Data Scraper and Analyzer")
    print("=" * 30)

    # 1. Fetch national data (non-Scrapy) and save
    national_data = run_legacy_scraper_for_national_data(config['scraper'])
    save_national_data_to_db(national_data)

    # 2. Fetch state-level data (Scrapy)
    run_scrapy_crawler()

    # 3. Fetch dynamic/table data (Selenium) and save
    print("\n--- Running Selenium Scraper for Population Data ---")
    # We target census years. Your election years are 2000, 2004, etc.
    # The closest census years are 2000, 2010, 2020.
    census_years = [2000, 2010, 2020]
    population_scraper = WikipediaPopulationScraper(headless=True)
    population_data = population_scraper.scrape(target_years=census_years)
    save_population_data_to_db(population_data)

    print("\n" + "-" * 30)
    print("Scraping complete. Data is now in the database.")
    print("Analyzing Data and Generating Reports...")
    print("-" * 30)

    os.makedirs(config['paths']['analysis_report_dir'], exist_ok=True)

    generate_analysis_reports(
        report_dir=config['paths']['analysis_report_dir'],
        bar_chart_filename=config['filenames']['bar_chart_report'],
        static_maps_filename=config['filenames']['static_maps_report'],
        template_config=config['templates']
    )

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds.")
    print("\nPipeline finished successfully!")
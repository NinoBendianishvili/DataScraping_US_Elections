import time
import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.settings import Settings

from src.data.database import get_db_connection, create_tables, save_national_data_to_db, save_fec_data_to_db
from src.analysis.reporter import generate_analysis_reports
from src.utils.config_loader import load_config
from src.scrapers.scrapy_crawler.election_crawler.spiders.state_spider import StateSpider
from src.scrapers.factory import ScraperFactory # Import the factory

def run_legacy_scraper_for_national_data(config):
    """Runs the original scraper to fetch ONLY national data using a factory."""
    print("--- Running Legacy Scraper for National Data ---")

    # --- FACTORY PATTERN IN ACTION ---
    # The main logic no longer knows about StateElectionScraper.
    # It just asks the factory for a "national" scraper.
    factory = ScraperFactory()
    scraper = factory.create_scraper("national", **config)

    scraper._fetch_all_national_data()
    return scraper.national_year_data

def run_scrapy_crawler():
    """Configures and runs the Scrapy crawler without changing directory."""
    print("--- Running Scrapy Crawler for State Data ---")

    sys.path.insert(0, os.path.join(os.getcwd(), 'src', 'scrapers', 'scrapy_crawler'))
    project_settings = get_project_settings()
    settings = Settings()
    settings.setmodule('election_crawler.settings', priority='project')
    process = CrawlerProcess(settings)
    process.crawl(StateSpider)
    process.start()
    sys.path.pop(0)

def main():
    """Main function to run the entire scraping and analysis pipeline."""
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

    # Instantiate the factory once for the pipeline
    scraper_factory = ScraperFactory()

    # 1. Fetch national data (non-Scrapy) and save
    national_data = run_legacy_scraper_for_national_data(config['scraper'])
    save_national_data_to_db(national_data)

    # 2. Fetch state-level data (Scrapy)
    run_scrapy_crawler()

    # 3. Fetch dynamic/table data (Selenium) and save
    print("\n--- Running Selenium Scraper for FEC Campaign Finance Data ---")
    # --- FACTORY PATTERN IN ACTION ---
    fec_scraper = scraper_factory.create_scraper(
        "fec",
        headless=True
    )
    fec_data = fec_scraper.scrape(target_years=config['scraper']['target_years'])
    save_fec_data_to_db(fec_data)

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
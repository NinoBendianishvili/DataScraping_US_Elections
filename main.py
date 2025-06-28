import time
import os
import sys
import logging
import concurrent.futures
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.settings import Settings

from src.scrapers.factory import ScraperFactory
from src.data.database import get_db_connection, create_tables, save_national_data_to_db, save_fec_data_to_db, save_turnout_data_to_db
from src.analysis.reporter import generate_analysis_reports
from src.utils.config_loader import load_config
from src.scrapers.scrapy_crawler.election_crawler.spiders.state_spider import StateSpider


def run_national_scraper_task(config):
    """Task for fetching national data."""
    print("--- [Thread] National Scraper started. ---")
    factory = ScraperFactory()
    scraper = factory.create_scraper("national", **config)
    scraper._fetch_all_national_data()
    print("--- [Thread] National Scraper finished. ---")
    return scraper.national_year_data

def run_fec_scraper_task(config):
    """Task for fetching FEC data with Selenium."""
    print("--- [Thread] FEC Selenium Scraper started. ---")
    factory = ScraperFactory()
    scraper = factory.create_scraper("fec", headless=True)
    fec_data = scraper.scrape(target_years=config['target_years'])
    print("--- [Thread] FEC Selenium Scraper finished. ---")
    return fec_data

def run_turnout_scraper_task(config):
    """Task for fetching Voter Turnout/Population data."""
    print("--- [Thread] Turnout Scraper started. ---")
    factory = ScraperFactory()
    scraper = factory.create_scraper("turnout")
    turnout_data = scraper.scrape(target_years=config['target_years'])
    print("--- [Thread] Turnout Scraper finished. ---")
    return turnout_data

def run_scrapy_task_in_main_thread():
    """Task for running the Scrapy crawler in the main thread."""
    print("--- [Main Thread] Scrapy Crawler started. ---")
    sys.path.insert(0, os.path.join(os.getcwd(), 'src', 'scrapers', 'scrapy_crawler'))
    project_settings = get_project_settings()
    settings = Settings()
    settings.setmodule('election_crawler.settings', priority='project')
    process = CrawlerProcess(settings)
    process.crawl(StateSpider)
    process.start()
    sys.path.pop(0)
    print("--- [Main Thread] Scrapy Crawler finished. ---")

def main():
    """Main function to run the entire scraping and analysis pipeline."""
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('webdriver_manager').setLevel(logging.WARNING)

    config = load_config()
    if config is None:
        sys.exit(1)

    conn = get_db_connection()
    create_tables(conn)
    conn.close()

    print("=" * 30)
    print("Starting Concurrent Scraping Pipeline")
    print("=" * 30)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_national = executor.submit(run_national_scraper_task, config['scraper'])
        future_fec = executor.submit(run_fec_scraper_task, config['scraper'])
        future_turnout = executor.submit(run_turnout_scraper_task, config['scraper'])

        run_scrapy_task_in_main_thread()

        print("Waiting for background scraper threads to complete...")
        national_data = future_national.result()
        fec_data = future_fec.result()
        turnout_data = future_turnout.result()

    print("\n" + "=" * 30)
    print("All Scraping Tasks Complete.")
    print("Saving data to the database...")
    print("=" * 30)

    save_national_data_to_db(national_data)
    save_fec_data_to_db(fec_data)
    save_turnout_data_to_db(turnout_data) # Call the new save function

    print("\n" + "-" * 30)
    print("Data is now in the database.")
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
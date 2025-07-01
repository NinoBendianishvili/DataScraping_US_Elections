import time
import os
import sys
import logging
import concurrent.futures
from concurrent.futures import as_completed

import click
from tqdm import tqdm
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.settings import Settings

from src.scrapers.factory import ScraperFactory
from src.data.database import get_db_connection, create_tables, save_national_data_to_db, save_fec_data_to_db, save_turnout_data_to_db
from src.analysis.reporter import generate_maps_report, generate_trends_report
from src.utils.config_loader import load_config
from src.scrapers.scrapy_crawler.election_crawler.spiders.state_spider import StateSpider


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


def run_national_scraper_task(config):
    """Task for fetching national data."""
    factory = ScraperFactory()
    scraper = factory.create_scraper("national", **config)
    scraper._fetch_all_national_data()
    return scraper.national_year_data

def run_fec_scraper_task(config):
    """Task for fetching FEC data with Selenium."""
    factory = ScraperFactory()
    scraper = factory.create_scraper("fec", headless=True)
    fec_data = scraper.scrape(target_years=config['target_years'])
    return fec_data

def run_turnout_scraper_task(config):
    """Task for fetching Voter Turnout/Population data."""
    factory = ScraperFactory()
    scraper = factory.create_scraper("turnout")
    turnout_data = scraper.scrape(target_years=config['target_years'])
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


@click.group()
def cli():
    pass


@cli.command()
def scrape():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(TqdmLoggingHandler())
    
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
    print("Step 1: Starting Concurrent Background Scrapers")
    print("=" * 30)

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_scraper = {
            executor.submit(run_national_scraper_task, config['scraper']): "national",
            executor.submit(run_fec_scraper_task, config['scraper']): "fec",
            executor.submit(run_turnout_scraper_task, config['scraper']): "turnout"
        }

        for future in tqdm(as_completed(future_to_scraper), total=len(future_to_scraper), desc="Processing background scrapers"):
            scraper_name = future_to_scraper[future]
            try:
                results[scraper_name] = future.result()
            except Exception as exc:
                logging.error(f'{scraper_name} scraper generated an exception: {exc}')
                results[scraper_name] = None
    
    print("\n" + "=" * 30)
    print("Step 2: Starting Main Thread Scrapy Crawler")
    print("=" * 30)
    
    run_scrapy_task_in_main_thread()

    print("\n" + "=" * 30)
    print("All Scraping Tasks Complete.")
    print("Saving data to the database...")
    print("=" * 30)

    national_data = results.get("national")
    fec_data = results.get("fec")
    turnout_data = results.get("turnout")

    if national_data is not None:
        save_national_data_to_db(national_data)
    if fec_data is not None:
        save_fec_data_to_db(fec_data)
    if turnout_data is not None:
        save_turnout_data_to_db(turnout_data)

    print("\n" + "-" * 30)
    print("Scraping and data storage complete.")
    print("-" * 30)


@cli.command()
def report():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = load_config()
    if config is None:
        sys.exit(1)

    print("\n" + "-" * 30)
    print("Analyzing Data and Generating Reports...")
    print("-" * 30)

    os.makedirs(config['paths']['analysis_report_dir'], exist_ok=True)
    generate_maps_report("analysis_report/election_maps.html")
    generate_trends_report("analysis_report/election_trends.html")
    print("Report generation complete.")


if __name__ == "__main__":
    start_time = time.time()
    cli()
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds.")
    print("\nPipeline finished successfully!")

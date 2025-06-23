import time
import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from src.scrapers.election_scraper import StateElectionScraper # Keep old scraper
from src.data.database import get_db_connection, create_tables
from src.analysis.reporter import generate_analysis_reports
from src.utils.config_loader import load_config
from src.scrapers.scrapy_crawler.election_crawler.spiders.state_spider import StateSpider

def run_legacy_scraper(config):
    """Runs the original scraper based on requests and BeautifulSoup."""
    print("--- Running Legacy Scraper ---")
    scraper = StateElectionScraper(
        target_years=config['target_years'],
        delay_seconds=config['delay_seconds'],
        max_workers=config['max_workers']
    )
    # The legacy scraper now only needs to fetch national data
    # as the state data is handled by Scrapy.
    scraper._fetch_all_national_data()


def run_scrapy_crawler():
    """Configures and runs the Scrapy crawler."""
    print("--- Running Scrapy Crawler for State Data ---")
    # Scrapy needs to be run from its project directory to find settings
    project_dir = os.path.join('src', 'scrapers', 'scrapy_crawler')
    os.chdir(project_dir)

    process = CrawlerProcess(get_project_settings())
    process.crawl(StateSpider)
    process.start() # The script will block here until the crawling is finished

    # Return to the original directory
    os.chdir(os.path.join('..', '..', '..'))


def main():
    """Main function to run the entire scraping and analysis pipeline."""
    config = load_config()
    if config is None:
        print("Configuration could not be loaded. Aborting execution.")
        sys.exit(1)

    # Set up the database
    conn = get_db_connection()
    create_tables(conn)
    conn.close()

    print("=" * 30)
    print("Starting Election Data Scraper and Analyzer")
    print("=" * 30)

    # --- RUN THE SCRAPERS ---
    # We can still run the old scraper to get national data
    run_legacy_scraper(config['scraper'])
    # Now run the new Scrapy crawler to get all state data
    run_scrapy_crawler()

    print("\n" + "-" * 30)
    print("Scraping complete. Data saved to database.")
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
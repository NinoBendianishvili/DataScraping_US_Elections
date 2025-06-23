import time
import os
import sys
from src.scrapers.election_scraper import StateElectionScraper
from src.data.database import get_db_connection, create_tables, save_results_to_db
from src.analysis.reporter import generate_analysis_reports
from src.utils.config_loader import load_config

def main():
    """Main function to run the entire scraping and analysis pipeline."""
    config = load_config()
    if config is None:
        print("Configuration could not be loaded. Aborting execution.")
        sys.exit(1)

    scraper_config = config['scraper']
    paths_config = config['paths']
    filenames_config = config['filenames']

    # --- NEW: Set up the database ---
    conn = get_db_connection()
    create_tables(conn)
    conn.close()

    print("=" * 30)
    print("Starting Election Data Scraper and Analyzer")
    print("=" * 30)

    scraper = StateElectionScraper(
        target_years=scraper_config['target_years'],
        delay_seconds=scraper_config['delay_seconds'],
        max_workers=scraper_config['max_workers']
    )
    all_results = scraper.scrape_all_states()

    if not all_results:
        print("Scraping finished, but no results were collected. Exiting.")
        return

    # --- CHANGE: Save to database instead of files ---
    print("\n" + "-" * 30)
    print("Saving Scraped Data to Database...")
    print("-" * 30)
    save_results_to_db(all_results)

    # ... The reporting section remains the same for now ...
    print("\n" + "-" * 30)
    print("Analyzing Data and Generating Reports...")
    print("-" * 30)

    os.makedirs(paths_config['analysis_report_dir'], exist_ok=True)

    generate_analysis_reports(
        # We will update this in the next step
        input_csv_path=None, # No longer reading from a CSV
        report_dir=paths_config['analysis_report_dir'],
        bar_chart_filename=filenames_config['bar_chart_report'],
        static_maps_filename=filenames_config['static_maps_report'],
        template_config=config['templates']
    )

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds.")
    print("\nPipeline finished successfully!")
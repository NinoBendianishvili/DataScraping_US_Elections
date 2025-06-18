import time
import os
import sys  # Import sys to exit gracefully
from src.scrapers.election_scraper import StateElectionScraper
from src.data.processors import save_to_csv, save_to_json
from src.analysis.reporter import generate_analysis_reports
from src.utils.config_loader import load_config

def main():
    """Main function to run the entire scraping and analysis pipeline."""

    # 1. Load Configuration
    config = load_config()

    # --- ADD THIS CHECK ---
    # If config loading fails, log_config already printed an error. Exit gracefully.
    if config is None:
        print("Configuration could not be loaded. Aborting execution.")
        sys.exit(1) # Exit with a non-zero status code to indicate an error
    # --- END OF CHECK ---

    scraper_config = config['scraper']
    paths_config = config['paths']
    filenames_config = config['filenames']

    print("=" * 30)
    print("Starting Election Data Scraper and Analyzer")
    print("=" * 30)

    # 2. Scrape Data
    scraper = StateElectionScraper(
        target_years=scraper_config['target_years'],
        delay_seconds=scraper_config['delay_seconds'],
        max_workers=scraper_config['max_workers']
    )
    all_results = scraper.scrape_all_states()

    if not all_results:
        print("Scraping finished, but no results were collected. Exiting.")
        return

    # 3. Process and Save Raw Data
    print("\n" + "-" * 30)
    print("Saving Raw Scraped Data...")
    print("-" * 30)

    # Ensure output directory exists
    os.makedirs(paths_config['data_output_dir'], exist_ok=True)

    csv_path = os.path.join(paths_config['data_output_dir'], filenames_config['csv_output'])
    json_path = os.path.join(paths_config['data_output_dir'], filenames_config['json_output'])

    save_to_csv(all_results, csv_path)
    save_to_json(all_results, json_path)

    # 4. Analyze Data and Generate Reports
    print("\n" + "-" * 30)
    print("Analyzing Data and Generating Reports...")
    print("-" * 30)

    # Ensure report directory exists
    os.makedirs(paths_config['analysis_report_dir'], exist_ok=True)

    generate_analysis_reports(
        input_csv_path=csv_path,
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
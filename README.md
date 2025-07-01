### Component Breakdown

-   **`main.py`**: The entry point of the application. It defines the `click` CLI commands (`scrape`, `report`) and orchestrates the entire pipeline.
-   **`src/scrapers/`**: Contains all scraping logic.
    -   `factory.py`: Implements the Factory pattern to create different scraper instances (`national`, `fec`, `turnout`).
    -   `election_scraper.py`: A robust scraper for national data using the `requests` library and the retry decorator.
    -   `selenium_fec_scraper.py`: A Selenium-based scraper for FEC data, handling dynamic content and pagination.
    -   `turnout_scraper.py`: A Selenium-based scraper for voter turnout data, handling nested iframes.
    -   `scrapy_crawler/`: A self-contained Scrapy project for crawling state-level data.
-   **`src/data/`**: Manages data persistence and modeling.
    -   `database.py`: Handles SQLite database connection, table creation, and data insertion logic.
    -   `models.py`: Defines data classes for structured, type-safe data handling.
-   **`src/analysis/`**: Contains the logic for generating reports.
    -   `reporter.py`: Queries the SQLite database with Pandas, processes the data, and uses Jinja2/Plotly to generate final HTML reports.
-   **`src/utils/`**: Provides shared utilities.
    -   `config_loader.py`: Loads project configurations from `config/settings.yaml`.
    -   `decorators.py`: Home to the `@retry_on_failure` decorator.

## Setup and Installation

**Prerequisites:**
- Python 3.9+
- Git

**Instructions:**

1.  **Clone the repository:**
    ```sh
    git clone <your-repo-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # On Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    The `webdriver-manager` library will automatically download and manage the correct ChromeDriver for Selenium, so no manual driver installation is needed.
    ```sh
    pip install -r requirements.txt
    ```

## Usage

The application is controlled via the command line.

1.  **Run the complete scraping pipeline:**
    This command will concurrently fetch all data from all sources and save it to `election_data.db` in the project root.
    ```sh
    python main.py scrape
    ```
    You will see progress bars for the background scrapers and logs from the main thread's Scrapy crawler.

2.  **Generate the analysis reports:**
    After the scraping is complete, run this command to analyze the data in the database and generate reports.
    ```sh
    python main.py report
    ```
    The reports will be saved in the `analysis_report/` directory:
    - `election_maps.html`
    - `election_trends.html`

3.  **View available commands:**
    ```sh
    python main.py --help
    ```
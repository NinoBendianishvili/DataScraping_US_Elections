# User Guide

## 1. Introduction

Welcome to the U.S. Election Data Scraper! This guide provides all the necessary steps to install, configure, and run the application to scrape election data and generate analysis reports.

## 2. Installation

Follow these steps to set up the project on your local machine.

### Prerequisites
- Python 3.8 or newer
- Git

### Setup Instructions
1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd DataScraping_US_Elections-final-project
    ```

2.  **Create and activate a virtual environment:**
    - On macOS/Linux:
      ```bash
      python3 -m venv .venv
      source .venv/bin/activate
      ```
    - On Windows:
      ```bash
      python -m venv .venv
      .\.venv\Scripts\activate
      ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

## 3. Configuration

The application's behavior can be customized via the `config.yaml` file located in the project root. This file allows you to change settings without modifying the source code.

Key settings include:
- `target_years`: A list of election years to scrape.
- `paths`: Directories for saving logs and reports.
- `filenames`: The output names for the generated HTML reports.
- `templates`: The names of the Jinja2 HTML templates used for reporting.

**Example `config.yaml` snippet:**
yaml
scraper:
  target_years: [2020, 2016, 2012, 2008, 2004, 2000]

paths:
  log_dir: "logs"
  analysis_report_dir: "analysis_report"

filenames:
  bar_chart_report: "election_analysis_report.html"
  static_maps_report: "election_static_maps_report.html"
## 4. `src.data` Module
Handles data storage and database interactions.

#### `database.py`
- **`DB_PATH`**: A constant pointing to the SQLite database file (`election_data.db`).
- **`get_db_connection()`**: Returns an `sqlite3.Connection` object to the database.
- **`create_tables()`**: Executes SQL `CREATE TABLE` statements to set up the database schema if it doesn't exist.
- **`save_national_data_to_db(data)`**: Saves national summary and state-level results to the `elections` and `results` tables.
- **`save_fec_data_to_db(data)`**: Saves candidate finance data to the `fec_data` table.
- **`save_turnout_data_to_db(data)`**: Saves voter turnout data to the `turnout` table.

---

## 5. `src.analysis` Module
Contains all logic for data analysis and visualization.

#### `reporter.py`
- **`generate_analysis_reports(...)`**: The primary public function. It orchestrates the entire reporting process, from loading data to rendering the final HTML files.
- **`_load_and_clean_data() -> pd.DataFrame`**: A helper function that executes a SQL query to join all relevant tables from the database into a single pandas DataFrame. It also performs critical cleaning and standardization steps, such as handling `NaN` values, standardizing state names (`str.title()`), and mapping party labels (`'DEMOCRAT'` -> `'Democratic'`).
- **`_create_national_trends_plot(df) -> str`**: Generates the HTML `div` for the national popular vote bar chart using Plotly.
- **`_create_election_map_plot(df, year) -> str`**: Generates the HTML `div` for the choropleth map of a single election year using Plotly.
- **`_render_and_save_report(...)`**: A utility function that uses Jinja2 to render a template with the provided context (containing plot divs) and save it as an HTML file.

---

## 6. `src.utils` Module
Contains utility functions used across the application.

#### `config_loader.py`
- **`load_config() -> dict`**: Reads the `config.yaml` file from the project root, parses it using `PyYAML`, and returns the contents as a Python dictionary.

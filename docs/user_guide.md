
# User Guide: US Election Data Scraping & Analysis System

## 1. Introduction

Welcome to the **US Election Data Scraping & Analysis System**! This guide walks you through setting up and using this powerful tool to collect, store, and analyze historical US presidential election data.

The system is a command-line application that automates a multi-stage data pipeline:

1. **Scrape**: Concurrently fetches data from multiple web sources, including national election results, FEC candidate filings, and state-level voter turnout statistics.  
2. **Store**: Cleans the collected data and stores it in a structured SQLite database (`election_data.db`).  
3. **Report**: Queries the database to perform data analysis and generates interactive HTML reports with charts and maps.

---

## 2. Prerequisites

Ensure the following are installed on your system:

- **Python 3.9+**
- **Git** (for cloning the repository)
- **Google Chrome** or **Mozilla Firefox** (required for the Selenium-based scraper)

---

## 3. Installation and Setup

### Step 1: Clone the Repository

Open your terminal and run:

```bash
git clone <your-repository-url>
cd DataScraping_US_Elections-final-project
```

### Step 2: Create a Virtual Environment

It’s recommended to use a Python virtual environment to avoid dependency conflicts.

```bash
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

You should see `(.venv)` at the beginning of your terminal prompt, indicating the environment is active.

### Step 3: Install Dependencies

Install all the required Python libraries:

```bash
pip install -r requirements.txt
```

The `webdriver-manager` library will handle browser driver downloads for Selenium.

### Step 4: Configure the Application (Optional)

You can modify `config/settings.yaml` to customize application behavior.

Example: To change the target election years:

```yaml
# config/settings.yaml
scraper:
  target_years: [2020, 2016, 2012, 2008, 2004, 2000]
  # ... other settings
```

---

## 4. Usage: Core Commands

Operate the application via the `main.py` script. There are two core commands:

### Command 1: `scrape`

Initiates the entire data collection and storage pipeline.

```bash
python main.py scrape
```

#### What to Expect:

- **Database Initialization**: Ensures `election_data.db` is ready.
- **Concurrent Scrapers**: Three parallel background threads fetch national data, FEC data, and voter turnout.
- **Scrapy Crawler**: Collects detailed state-by-state results.
- **Data Saving**: All data is stored in `election_data.db`.

You'll see:

```
Scraping and data storage complete
```

### Command 2: `report`

Uses the stored data to generate HTML reports.

```bash
python main.py report
```

#### What to Expect:

- Reads all data from `election_data.db`.
- Performs analysis and creates visualizations.
- Saves output to `data_output/reports/`:

#### Output Files:

- `bar_chart_report.html`: Interactive national and state vote trends.
- `static_maps_report.html`: Interactive US choropleth maps for each election year.

Open these HTML files in your browser to view the results.

---

## 5. Typical Workflow

1. **Set up the project** (see installation instructions).
2. **Run the scraper**:

    ```bash
    python main.py scrape
    ```

3. **Generate reports**:

    ```bash
    python main.py report
    ```

4. **View results** in `data_output/reports/`.

---

## 6. Troubleshooting

- **Selenium/WebDriver Errors**:
  - Make sure Chrome/Firefox is up to date.
  - `webdriver-manager` should handle drivers, but manual installation may be needed in restricted environments.

- **Scraper Fails**:
  - Web page structure might have changed.
  - Update logic in `src/scrapers/parsers.py`.

- **Firewall/Network Issues**:
  - Ensure internet access and that firewalls aren't blocking connections.

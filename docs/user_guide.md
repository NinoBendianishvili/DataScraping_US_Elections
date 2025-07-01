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
```yaml
scraper:
  target_years: [2020, 2016, 2012, 2008, 2004, 2000]

paths:
  log_dir: "logs"
  analysis_report_dir: "analysis_report"

filenames:
  bar_chart_report: "election_analysis_report.html"
  static_maps_report: "election_static_maps_report.html"
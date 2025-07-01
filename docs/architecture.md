# System Architecture

## 1. Introduction

This document outlines the technical architecture of the U.S. Election Data Scraping and Analysis System. The system is designed to be a modular, scalable, and robust pipeline for collecting election data from multiple disparate sources, processing it, and generating insightful reports with visualizations.

The architecture addresses several key challenges:
- **Diverse Data Sources**: Handling static HTML, dynamic JavaScript-rendered pages, and potentially JSON APIs.
- **Performance**: Utilizing concurrency to speed up the I/O-bound scraping process.
- **Maintainability**: Decoupling components through a modular structure and design patterns.
- **Configuration**: Allowing easy modification of parameters (like target years or file paths) without changing the source code.

## 2. Core Components

The system is organized into several distinct layers, each with a specific responsibility.

### 2.1. Orchestration and CLI (`main.py`)
The main entry point of the application. It uses the `click` library to create a command-line interface (CLI) that orchestrates the entire pipeline. It serves as the top-level controller, delegating tasks to the scraping and analysis modules.

### 2.2. Data Collection (`src/scrapers/`)
This layer is responsible for all data extraction activities. A **Factory Design Pattern** (`factory.py`) is used to instantiate the appropriate scraper on demand, which decouples the main application from the specific implementation details of each scraper.

- **`StateSpider` (Scrapy)**: A Scrapy-based crawler designed for deeply nested or complex websites. It manages its own requests, processing, and data extraction pipeline, saving results directly to the database via a Scrapy Item Pipeline.
- **`selenium_fec_scraper.py`**: A Selenium-based scraper for handling dynamic websites that require browser automation to render JavaScript, interact with forms (like year selection dropdowns), and handle client-side pagination.
- **`turnout_scraper.py` & `election_scraper.py`**: Static scrapers that use libraries like `requests` and `BeautifulSoup4` to parse simple HTML content. These are suitable for websites that do not rely heavily on client-side JavaScript.

### 2.3. Data Persistence (`src/data/`)
This layer handles all interactions with the database.

- **`database.py`**: A data access module that abstracts all database operations. It is responsible for:
    - Establishing a connection to the SQLite database (`election_data.db`).
    - Defining and creating the database schema (`elections`, `results`, `states`, `fec_data`, `turnout` tables).
    - Saving the structured data received from the various scrapers into the appropriate tables using `pandas`.
- **`models.py`**: Defines data structures (e.g., Pydantic models or dataclasses) for data consistency between the scraping and database layers.

### 2.4. Data Analysis and Reporting (`src/analysis/`)
This layer is responsible for transforming raw data into meaningful insights.

- **`reporter.py`**: The core analysis engine. It queries the SQLite database, uses `pandas` for data cleaning and transformation (e.g., standardizing state names and party labels), and generates visualizations.
- **`plotly`**: Used to create interactive charts and maps (bar charts, choropleth maps).
- **`Jinja2`**: A templating engine used to inject the generated plots and data into pre-defined HTML templates (`templates/`), producing the final, polished reports.

### 2.5. Utilities (`src/utils/`)
- **`config_loader.py`**: A simple module to load all system settings from an external `config.yaml` file, promoting a clean separation of configuration from code.

## 3. Data Flow

The system operates in two main phases, initiated by the user via the CLI.

**Phase 1: Scraping (`python main.py scrape`)**
1. The `scrape` command is executed.
2. The database schema is created if it doesn't exist.
3. The `ThreadPoolExecutor` is used to launch the I/O-bound Selenium and static scrapers concurrently.
4. The Scrapy crawler runs in the main thread, managing its own asynchronous operations.
5. Each scraper collects its data, structures it, and calls the appropriate function in `database.py` to save the results.
6. Progress is tracked in the console using `tqdm`, which is integrated with a custom logging handler to prevent output corruption.

**Phase 2: Reporting (`python main.py report`)**
1. The `report` command is executed.
2. The `reporter.py` module queries the `election_data.db` database, joining tables to create a comprehensive DataFrame.
3. The data is cleaned and standardized (e.g., converting state abbreviations, handling missing values).
4. Plotly is used to generate HTML `div`s for each required visualization (national trends, state maps, etc.).
5. The Jinja2 templating engine renders the final HTML report files by injecting the plot `div`s into the appropriate templates.
6. The final HTML files are saved to the `analysis_report/` directory.

## 4. Concurrency Model

Concurrency is achieved using Python's `concurrent.futures.ThreadPoolExecutor`. This is ideal for web scraping, as the tasks are I/O-bound (waiting for network responses) rather than CPU-bound. By running multiple scrapers in parallel, the total collection time is significantly reduced. The Scrapy crawler uses its own built-in asynchronous networking engine (Twisted) and is therefore run separately.
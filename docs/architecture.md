# Technical Architecture: US Election Data Scraping & Analysis System

## 1. Introduction

This document outlines the technical architecture of the US Election Data Scraping & Analysis System. The project's primary goal is to create a robust, modular, and automated pipeline for collecting historical US presidential election data from various web sources, processing it, persisting it in a structured database, and generating insightful analytical reports with data visualizations.

The system is built entirely in Python, leveraging a modern stack of libraries for web scraping, data manipulation, and reporting. The architecture is designed with key principles in mind: separation of concerns, configuration-driven operation, robustness, and testability. This modular design ensures that each component of the system can be developed, tested, and maintained independently.

The pipeline ingests data from static and dynamic web pages, cleans and structures it into a unified format, stores it in an SQLite database, and produces interactive HTML reports featuring national trends, state-level analysis, and choropleth maps.

## 2. Core Architectural Principles

The system's design is guided by several fundamental software engineering principles:

*   **Modularity & Separation of Concerns:** The project is strictly organized into distinct layers, each with a single responsibility. The `src` directory is divided into `scrapers` (data acquisition), `data` (modeling, persistence, and serialization), `analysis` (processing and reporting), and `utils` (shared helpers). This separation simplifies development, debugging, and future enhancements.
*   **Configuration-Driven Design:** Core operational parameters, such as target URLs, timeouts, and output paths, are externalized into a `config/settings.yaml` file. The `src/utils/config_loader.py` provides a centralized mechanism for accessing these settings, allowing the system's behavior to be modified without changing the source code.
*   **Robustness and Resilience:** The system is designed to handle real-world challenges of web scraping. The `retry_on_failure` decorator in `src/utils/decorators.py` provides an automatic, exponential-backoff retry mechanism for network-related errors, making the data collection process more resilient to transient failures.
*   **Data-Centric Modeling:** A clear and strongly-typed data model, defined in `src/data/models.py`, serves as the canonical representation of information within the system. Using dedicated classes (`StateData`, `YearData`, `ElectionResult`) instead of simple dictionaries ensures data consistency, validation, and clarity throughout the pipeline.
*   **Testability:** The modular design directly supports comprehensive testing. Components with pure logic (e.g., parsers, model validators, data processors) are decoupled from components with side effects (e.g., network requests, database writes). This allows for effective unit testing using `pytest` and mocking libraries to isolate components and verify their correctness.

## 3. Component Breakdown

The system is composed of several collaborating components, each residing within the `src` directory.

### 3.1. `main.py`: The Orchestrator

This is the main entry point of the application. Its responsibilities include:
*   Parsing command-line arguments to determine the desired action (e.g., scrape, report).
*   Loading the application configuration using `config_loader`.
*   Initializing the logging system.
*   Orchestrating the main workflow by invoking the appropriate components from the `scrapers` and `analysis` layers in the correct sequence.

### 3.2. Data Collection Layer (`src/scrapers/`)

This layer is responsible for all data acquisition tasks. It employs multiple techniques to handle different types of web sources.

*   **Parsing Strategies (`parsers.py`):** This module implements the **Strategy Design Pattern**. The `ParsingStrategy` abstract base class defines a common `parse` interface. Concrete classes, like `NationalPageParsingStrategy`, provide specific implementations for extracting data from different page layouts. This makes the system extensible; adding a parser for a new website simply requires creating a new strategy class.
*   **Scraper Implementations:** The directory is designed to hold various scraper types:
    *   **Static Scrapers:** Use `requests` and `BeautifulSoup4` for simple, static HTML pages.
    *   **Dynamic Scrapers (`selenium_fec_scraper.py`):** Use `Selenium` to automate a web browser for scraping content rendered by JavaScript.
    *   **Framework-based Crawlers (`scrapy_crawler/`):** Use the `Scrapy` framework for efficiently crawling multiple pages on a single, complex site.
*   **Scraper Factory (`factory.py`):** This component (inferred from the project structure) implements the **Factory Design Pattern**. It is responsible for instantiating the correct scraper (static, dynamic, or Scrapy) based on a given target or configuration, decoupling the orchestrator from the concrete scraper implementations.
*   **Resilience (`decorators.py`):** The `retry_on_failure` decorator is applied to network-facing functions within the scrapers to handle HTTP errors, timeouts, and other connection issues gracefully.

### 3.3. Data Management & Persistence Layer (`src/data/`)

This layer defines the structure of the data and handles how it is stored and serialized.

*   **Data Models (`models.py`):** This is the heart of the data layer. It defines the core objects:
    *   `Party`: An `Enum` for type-safe representation of political parties.
    *   `StateData`: Holds state-specific information.
    *   `YearData`: Contains national-level data for a given election, including vote cleaning logic.
    *   `ElectionResult`: The central object that links state and year data, providing a complete record for a single state in a single election. Input validation is built into the `__init__` methods to ensure data integrity from the moment of creation.
*   **Database (`database.py`):** This module abstracts all interaction with the SQLite database. It is responsible for establishing connections, creating the necessary tables (schema), and providing functions to insert, update, and query election data. Using a database instead of flat files allows for more efficient querying and serves as a single source of truth for the analysis layer.
*   **Data Processors (`processors.py`):** These functions act as data serializers. They take lists of `ElectionResult` objects from memory and convert them into standard file formats like CSV and JSON for easy export or for consumption by other tools.

### 3.4. Analysis & Reporting Layer (`src/analysis/`)

This is the final stage of the pipeline, responsible for turning raw data into meaningful insights.

*   **Report Generator (`reporter.py`):** This powerful module orchestrates the entire analysis and visualization process.
    1.  It connects to the SQLite database to fetch the consolidated, clean data.
    2.  It loads the data into a `pandas` DataFrame, the industry standard for data manipulation in Python.
    3.  It performs data cleaning, transformation, and aggregation (e.g., calculating national vote shares, grouping by year).
    4.  It uses the `Plotly` library to generate interactive charts and maps (bar charts for trends, choropleth maps for geographical results).
    5.  It uses the `Jinja2` templating engine to inject the generated plots and data tables into pre-defined HTML templates.
    6.  The final, rendered HTML is saved to the `data_output/reports/` directory.

## 4. Data Flow

The system operates as a sequential pipeline:

1.  **Execution:** The user runs `python main.py [command]`.
2.  **Configuration:** `main.py` loads settings from `config/settings.yaml`.
3.  **Scraping:** The appropriate scraper is invoked. It fetches web content (HTML).
4.  **Parsing:** The corresponding parsing strategy is applied to the HTML, extracting raw key-value data.
5.  **Modeling:** The raw data is validated and instantiated into a list of `ElectionResult` objects.
6.  **Persistence:** The `database.py` module takes the `ElectionResult` objects and writes their contents into the `results`, `states`, and `elections` tables in the SQLite database.
7.  **Reporting:** When the `report` command is issued, `reporter.py` is triggered.
8.  **Data Loading:** The reporter queries the SQLite database to load all relevant data into a Pandas DataFrame.
9.  **Analysis & Visualization:** The DataFrame is used to generate analytical summaries and Plotly visualizations.
10. **Rendering:** The visualizations and data are rendered into an HTML file using Jinja2 templates.
11. **Output:** The final HTML report is saved to disk.


## 5. Dependencies and Environment

The project relies on a set of well-established open-source libraries, managed via `requirements.txt`.

*   **Core Scraping:** `requests`, `beautifulsoup4`, `scrapy`
*   **Dynamic Scraping:** `selenium`, `webdriver-manager`
*   **Data & Analysis:** `pandas`, `plotly`
*   **Utilities:** `PyYAML` (config), `jinja2` (templating), `click` (CLI)
*   **Testing:** `pytest`, `pytest-mock`

The entire project is intended to be run within a dedicated Python virtual environment (`.venv`) to ensure dependency isolation and reproducibility.

## 6. Potential Improvements

*   **Scalability:** For larger-scale operations, the SQLite database could be upgraded to a client-server database like **PostgreSQL**, which offers better concurrency and performance.
*   **Distributed Scraping:** Implement a task queue like **Celery** with **Redis** to distribute scraping jobs across multiple workers, significantly speeding up data collection.
*   **Containerization:** The entire application could be containerized using **Docker**, simplifying deployment and ensuring a consistent runtime environment across different machines.
*   **CI/CD Pipeline:** A GitHub Actions workflow could be established to automatically run the `pytest` suite on every push, ensuring code quality and preventing regressions.
*   **API Layer:** A lightweight web framework like **FastAPI** could be added to expose the cleaned data via a REST API, allowing other services to consume the election data programmatically.

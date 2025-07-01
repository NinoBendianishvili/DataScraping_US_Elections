# Team Contributions

This project was a collaborative effort by **Nikoloz Topuridze** and **Nino Bendianishvili**. The development work was divided based on architectural layers and specific technical challenges, ensuring a comprehensive and well-structured final product.

---

### Nikoloz Topuridze

Nikoloz focused on the high-level architecture, pipeline orchestration, and the implementation of complex, dynamic web scrapers. His responsibilities were centered around creating a robust, efficient, and scalable data extraction framework.

-   **Core Architecture & Pipeline Orchestration:**
    -   Designed the overall data flow and project structure.
    -   Implemented the main orchestrator in `main.py`, including the `concurrent.futures.ThreadPoolExecutor` to manage parallel scraping tasks.
    -   Developed the `click`-based Command-Line Interface (CLI) for user-friendly interaction.

-   **Dynamic and Background Scraping:**
    -   Implemented the **Selenium-based scrapers** (`selenium_fec_scraper.py`, `turnout_scraper.py`) for handling JavaScript-heavy websites.
    -   Engineered solutions for complex web interactions, such as handling dynamic loading overlays, paginated tables, and nested `iframes`.
    -   Developed the `requests`-based national scraper (`election_scraper.py`) and integrated it into the concurrent execution model.

-   **Design Patterns & Reusability:**
    -   Introduced the **Factory and Strategy design patterns** (`factory.py`, `parsers.py`) to decouple scraper instantiation and parsing logic, making the system modular and extensible.
    -   Created the generic `@retry_on_failure` decorator (`decorators.py`) to improve the fault tolerance of all network-facing components.

---

### Nino Bendianishvili

Nino focused on the data persistence layer, the structured web crawling component, and the final data analysis and visualization. Her work ensured that the collected data was accurately modeled, stored, and transformed into insightful reports.

-   **Database Design and Management:**
    -   Designed the normalized **SQLite database schema** (`database.py`), defining tables for states, elections, results, finances, and turnout statistics.
    -   Wrote the data insertion logic to handle `INSERT OR REPLACE` operations, ensuring data integrity and preventing duplicates.
    -   Integrated the database functions with all scrapers.

-   **Structured Crawling with Scrapy:**
    -   Developed the entire **Scrapy project** (`src/scrapers/scrapy_crawler/`) to efficiently crawl state-level election data from 270toWin.com.
    -   Defined Scrapy items (`items.py`) for structured data extraction and implemented a custom Scrapy pipeline (`pipelines.py`) to write scraped data directly to the SQLite database.
    -   Ensured the Scrapy crawler was seamlessly integrated and executed from the main pipeline orchestrator.

-   **Data Modeling and Reporting:**
    -   Created the core data model classes (`models.py`) to enforce data structure and type safety across the application.
    -   Implemented the **analysis and reporting module** (`reporter.py`), which queries the database using Pandas.
    -   Used **Plotly** and **Jinja2** to generate interactive HTML reports, including choropleth maps and trend charts, providing a clear visual summary of the scraped data.
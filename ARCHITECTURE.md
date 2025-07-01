## Project Structure
Use code with caution.
```
├── analysis_report/ # Output directory for HTML reports
├── config/
│ └── settings.yaml # Project configuration file
├── src/
│ ├── analysis/
│ │ └── reporter.py # Logic for generating reports
│ ├── data/
│ │ ├── database.py # Database schema and save functions
│ │ └── models.py # Pydantic-style data models
│ ├── scrapers/
│ │ ├── scrapy_crawler/ # Scrapy project for state data
│ │ ├── election_scraper.py
│ │ ├── factory.py
│ │ ├── parsers.py
│ │ ├── selenium_fec_scraper.py
│ │ └── turnout_scraper.py
│ └── utils/
│ ├── config_loader.py
│ └── decorators.py
├── main.py # Main entrypoint with Click CLI
├── requirements.txt
└── README.md
```
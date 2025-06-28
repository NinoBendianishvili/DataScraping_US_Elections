"""
Implements the Factory Design Pattern for creating scraper objects.

This factory centralizes the logic for instantiating different scraper objects,
decoupling the main application from the concrete scraper classes.
"""
from typing import Dict, Any, Type

from src.scrapers.election_scraper import StateElectionScraper
from src.scrapers.selenium_fec_scraper import FECScraper
from src.scrapers.turnout_scraper import TurnoutScraper

from .election_scraper import StateElectionScraper
from .selenium_fec_scraper import FECScraper
from .turnout_scraper import TurnoutScraper  # Import the new scraper
from .parsers import ParsingStrategy, NationalPageParsingStrategy

# A type hint for our scraper classes
ScraperClass = Type[StateElectionScraper] | Type[FECScraper] | Type[TurnoutScraper]

class ScraperFactory:
    """
    The factory for creating scrapers. It knows how to build each scraper,
    including injecting the correct parsing strategy where needed.
    """
    def create_scraper(self, scraper_type: str, **kwargs: Any) -> FECScraper | StateElectionScraper | TurnoutScraper:
        """
        Creates and returns a scraper instance based on the given type.

        Args:
            scraper_type (str): The type of scraper to create ('national', 'fec', 'turnout').
            **kwargs: Configuration arguments for the scraper.

        Returns:
            An instance of a scraper class.

        Raises:
            ValueError: If an unknown scraper_type is provided.
        """
        if scraper_type == "national":
            national_parsing_strategy: ParsingStrategy = NationalPageParsingStrategy()
            return StateElectionScraper(
                parsing_strategy=national_parsing_strategy,
                **kwargs
            )
        elif scraper_type == "fec":
            return FECScraper(**kwargs)

        elif scraper_type == "turnout":
            return TurnoutScraper(**kwargs)

        else:
            raise ValueError(f"Unknown scraper type: '{scraper_type}'")
"""
Defines the core data models for the election scraping project, including data
structures for states, election years, and individual election results.
"""

import re
from enum import Enum
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

class Party(Enum):
    """Enumeration for political parties."""
    DEMOCRATIC = "Democratic"
    REPUBLICAN = "Republican"
    OTHER = "Other"

class StateData:
    """Holds information specific to a US State: name and electoral votes."""
    def __init__(self, state_name: str, electoral_votes: Optional[int] = None, **kwargs):
        if not state_name or not isinstance(state_name, str):
            raise ValueError("State name must be a non-empty string.")
        self.state_name: str = state_name

        if electoral_votes is not None and not isinstance(electoral_votes, int):
            raise TypeError(f"Electoral votes must be an integer, got {type(electoral_votes)}.")
        self.electoral_votes: Optional[int] = electoral_votes

    def __repr__(self) -> str:
        return f"StateData(name='{self.state_name}', EV={self.electoral_votes})"

class YearData:
    """Holds information specific to an election year: candidates and national votes."""
    def __init__(self, year: int, dem_leader: Optional[str] = None, rep_leader: Optional[str] = None,
                 dem_votes: Optional[Union[int, str]] = None, rep_votes: Optional[Union[int, str]] = None, **kwargs):
        if not isinstance(year, int):
            raise TypeError(f"Election year must be an integer, got {type(year)}.")
        self.year: int = year
        self.dem_leader: Optional[str] = dem_leader
        self.rep_leader: Optional[str] = rep_leader
        self.dem_votes: Optional[int] = self._clean_vote_string(dem_votes, "Democratic National", year)
        self.rep_votes: Optional[int] = self._clean_vote_string(rep_votes, "Republican National", year)

    def _clean_vote_string(self, votes: Optional[Union[int, str]], vote_type: str, year: int) -> Optional[int]:
        """Cleans a string containing commas and converts to an integer."""
        if votes is None:
            return None
        if isinstance(votes, int):
            return votes
        if isinstance(votes, str):
            try:
                cleaned_votes = re.sub(r'[,\s]', '', votes)
                return int(cleaned_votes)
            except (ValueError, TypeError):
                logger.warning(f"Could not parse vote string '{votes}' for {vote_type} in {year}. Storing None.")
                return None
        return None

    @property
    def total_national_votes(self) -> Optional[int]:
        """Calculates total national votes if both party votes are available."""
        if self.dem_votes is not None and self.rep_votes is not None:
            return self.dem_votes + self.rep_votes
        return None

    def __repr__(self) -> str:
        return (f"YearData(year={self.year}, DEM='{self.dem_leader}', REP='{self.rep_leader}', "
                f"DEM_Votes={self.dem_votes}, REP_Votes={self.rep_votes})")

class ElectionResult:
    """Links state data, year data, and state-level election percentages."""
    def __init__(self, state_info: StateData, year_info: YearData,
                 dem_percentage: Optional[float] = None, rep_percentage: Optional[float] = None,
                 winner: Optional[Party] = None):
        if not isinstance(state_info, StateData):
            raise TypeError("state_info must be a StateData instance.")
        if not isinstance(year_info, YearData):
            raise TypeError("year_info must be a YearData instance.")
            
        self.state_info = state_info
        self.year_info = year_info
        self.dem_percentage = self._validate_percentage(dem_percentage, "Democratic")
        self.rep_percentage = self._validate_percentage(rep_percentage, "Republican")
        self.winner = winner

    def _validate_percentage(self, percent: Optional[float], party: str) -> Optional[float]:
        """Validates that a percentage is a float between 0 and 100."""
        if percent is not None:
            if not isinstance(percent, (int, float)):
                raise TypeError(f"{party} percentage must be numeric.")
            if not (0 <= percent <= 100.1): # Allow slight overage for rounding
                logger.warning(f"{party} percentage {percent} is outside the 0-100 range.")
        return percent

    def __repr__(self) -> str:
        return (f"ElectionResult(State='{self.state_info.state_name}', Year={self.year_info.year}, "
                f"DEM%={self.dem_percentage}, REP%={self.rep_percentage}, "
                f"Winner={self.winner.value if self.winner else 'N/A'})")
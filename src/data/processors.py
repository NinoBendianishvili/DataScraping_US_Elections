"""
Functions for processing and saving scraped data to various file formats.
"""
import csv
import json
import os
import logging
from typing import List, Dict, Any

from .models import ElectionResult

logger = logging.getLogger(__name__)

def _ensure_dir_exists(filepath: str):
    """Creates the directory for a given filepath if it doesn't exist."""
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)

def save_to_csv(results: List[ElectionResult], filepath: str):
    """Saves a list of ElectionResult objects to a CSV file."""
    if not results:
        logger.warning("No results to save to CSV.")
        return

    _ensure_dir_exists(filepath)
    logger.info(f"Saving {len(results)} results to CSV: {filepath}")

    header = [
        'year', 'state_name', 'electoral_votes', 'state_winner', 
        'dem_state_percentage', 'rep_state_percentage',
        'dem_leader', 'rep_leader',
        'dem_national_votes', 'rep_national_votes', 'total_national_votes'
    ]

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()
            for result in results:
                writer.writerow({
                    'year': result.year_info.year,
                    'state_name': result.state_info.state_name,
                    'electoral_votes': result.state_info.electoral_votes,
                    'state_winner': result.winner.value if result.winner else None,
                    'dem_state_percentage': result.dem_percentage,
                    'rep_state_percentage': result.rep_percentage,
                    'dem_leader': result.year_info.dem_leader,
                    'rep_leader': result.year_info.rep_leader,
                    'dem_national_votes': result.year_info.dem_votes,
                    'rep_national_votes': result.year_info.rep_votes,
                    'total_national_votes': result.year_info.total_national_votes,
                })
        logger.info("Successfully saved data to CSV.")
    except (IOError, csv.Error) as e:
        logger.error(f"Error writing to CSV file {filepath}: {e}", exc_info=True)

def _convert_result_to_dict(result: ElectionResult) -> Dict[str, Any]:
    """Converts an ElectionResult object to a dictionary for JSON serialization."""
    return {
        "year": result.year_info.year,
        "state": result.state_info.state_name,
        "electoral_votes": result.state_info.electoral_votes,
        "national_candidates": {
            "democrat": result.year_info.dem_leader,
            "republican": result.year_info.rep_leader,
        },
        "national_popular_vote": {
            "democrat": result.year_info.dem_votes,
            "republican": result.year_info.rep_votes,
            "total": result.year_info.total_national_votes,
        },
        "state_results": {
            "winner": result.winner.value if result.winner else None,
            "dem_percentage": result.dem_percentage,
            "rep_percentage": result.rep_percentage,
        }
    }

def save_to_json(results: List[ElectionResult], filepath: str):
    """Saves a list of ElectionResult objects to a JSON file."""
    if not results:
        logger.warning("No results to save to JSON.")
        return

    _ensure_dir_exists(filepath)
    logger.info(f"Saving {len(results)} results to JSON: {filepath}")

    data_to_save = [_convert_result_to_dict(result) for result in results]

    try:
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data_to_save, jsonfile, indent=4)
        logger.info("Successfully saved data to JSON.")
    except (IOError, TypeError) as e:
        logger.error(f"Error writing to JSON file {filepath}: {e}", exc_info=True)
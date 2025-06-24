"""
Handles all database operations for the election scraper project,
including creating tables and inserting data.
"""
import sqlite3
import logging
from typing import List, Dict

from .models import ElectionResult

logger = logging.getLogger(__name__)
DB_PATH = "election_data.db"

def get_db_connection() -> sqlite3.Connection:
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(conn: sqlite3.Connection):
    """Creates the necessary database tables if they don't already exist."""
    logger.info("Setting up database tables...")
    try:
        cursor = conn.cursor()

        # States Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS states (
                state_name TEXT PRIMARY KEY NOT NULL,
                electoral_votes INTEGER
            );
        """)

        # Elections Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS elections (
                year INTEGER PRIMARY KEY NOT NULL,
                dem_leader TEXT,
                rep_leader TEXT,
                dem_national_votes INTEGER,
                rep_national_votes INTEGER,
                total_national_votes INTEGER
            );
        """)

        # Results Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_name TEXT NOT NULL,
                year INTEGER NOT NULL,
                dem_state_percentage REAL,
                rep_state_percentage REAL,
                state_winner TEXT,
                FOREIGN KEY (state_name) REFERENCES states (state_name),
                FOREIGN KEY (year) REFERENCES elections (year),
                UNIQUE(state_name, year)
            );
        """)

        # Population table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state_populations (
                state_name TEXT NOT NULL,
                year INTEGER NOT NULL,
                population INTEGER,
                PRIMARY KEY (state_name, year),
                FOREIGN KEY (state_name) REFERENCES states (state_name)
            );
        """)

        conn.commit()
        logger.info("Database tables are ready.")
    except sqlite3.Error as e:
        logger.error(f"Database error during table creation: {e}", exc_info=True)
        conn.rollback()

def save_national_data_to_db(national_data: dict):
    """Saves the national election year data to the 'elections' table."""
    if not national_data:
        logger.warning("No national data provided to save to the database.")
        return

    logger.info("Saving national election data to the database...")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        for year, data in national_data.items():
            cursor.execute(
                """INSERT OR REPLACE INTO elections (year, dem_leader, rep_leader, 
                                                   dem_national_votes, rep_national_votes, total_national_votes) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    year, data.get('dem_leader'), data.get('rep_leader'),
                    data.get('dem_votes'), data.get('rep_votes'), data.get('total_national_votes')
                )
            )
        conn.commit()
        logger.info("Successfully saved national data.")
    except sqlite3.Error as e:
        logger.error(f"Database error during national data insertion: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()

def save_population_data_to_db(population_data: List[Dict]):
    """Saves the scraped population data to the database."""
    if not population_data:
        logger.warning("No population data provided to save.")
        return

    logger.info(f"Saving {len(population_data)} population records to the database...")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        for item in population_data:
            cursor.execute(
                "INSERT OR REPLACE INTO state_populations (state_name, year, population) VALUES (?, ?, ?)",
                (item['state_name'], item['year'], item['population'])
            )
        conn.commit()
        logger.info("Successfully saved all population data.")
    except sqlite3.Error as e:
        logger.error(f"Database error during population data insertion: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()
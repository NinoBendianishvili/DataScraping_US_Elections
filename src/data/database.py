"""
Handles all database operations for the election scraper project,
including creating tables and inserting data.
"""
import sqlite3
import logging
from typing import List

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
        conn.commit()
        logger.info("Database tables are ready.")
    except sqlite3.Error as e:
        logger.error(f"Database error during table creation: {e}", exc_info=True)
        conn.rollback()

def save_results_to_db(results: List[ElectionResult]):
    """
    Saves a list of ElectionResult objects to the database, handling
    insertions into normalized tables.
    """
    if not results:
        logger.warning("No results to save to the database.")
        return

    logger.info(f"Saving {len(results)} results to the database...")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        for result in results:
            # Insert state data (will be ignored if it already exists)
            cursor.execute(
                "INSERT OR IGNORE INTO states (state_name, electoral_votes) VALUES (?, ?)",
                (result.state_info.state_name, result.state_info.electoral_votes)
            )

            # Insert election year data (will be ignored if it already exists)
            cursor.execute(
                """INSERT OR IGNORE INTO elections (year, dem_leader, rep_leader, 
                                                  dem_national_votes, rep_national_votes, total_national_votes) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    result.year_info.year, result.year_info.dem_leader, result.year_info.rep_leader,
                    result.year_info.dem_votes, result.year_info.rep_votes, result.year_info.total_national_votes
                )
            )

            # Insert the specific result (linking state and year)
            cursor.execute(
                """INSERT OR REPLACE INTO results (state_name, year, dem_state_percentage, 
                                                 rep_state_percentage, state_winner) 
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    result.state_info.state_name, result.year_info.year,
                    result.dem_percentage, result.rep_percentage,
                    result.winner.value if result.winner else None
                )
            )

        conn.commit()
        logger.info("Successfully saved all results to the database.")
    except sqlite3.Error as e:
        logger.error(f"Database error during insertion: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()
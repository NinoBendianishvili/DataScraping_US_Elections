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

        # Existing tables...
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS states (
                state_name TEXT PRIMARY KEY NOT NULL,
                electoral_votes INTEGER
            );
        """)
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fec_candidate_receipts (
                candidate_name TEXT NOT NULL,
                election_year INTEGER NOT NULL,
                party TEXT,
                total_receipts REAL,
                PRIMARY KEY (candidate_name, election_year)
            );
        """)

        # --- NEW TABLE FOR TURNOUT STATISTICS ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS turnout_statistics (
                state TEXT NOT NULL,
                year INTEGER NOT NULL,
                voting_eligible_population INTEGER,
                voting_age_population INTEGER,
                prison INTEGER,
                probation INTEGER,
                parole INTEGER,
                total_ineligible_felon INTEGER,
                overseas_eligible INTEGER,
                PRIMARY KEY (state, year)
            );
        """)

        conn.commit()
        logger.info("Database tables are ready.")
    except sqlite3.Error as e:
        logger.error(f"Database error during table creation: {e}", exc_info=True)
        conn.rollback()

def save_national_data_to_db(national_data: dict):
    # ... (no changes to this function)
    if not national_data: return
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        for year, data in national_data.items():
            cursor.execute(
                """INSERT OR REPLACE INTO elections (year, dem_leader, rep_leader, dem_national_votes, rep_national_votes, total_national_votes) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (year, data.get('dem_leader'), data.get('rep_leader'), data.get('dem_votes'), data.get('rep_votes'), data.get('total_national_votes'))
            )
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error during national data insertion: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()

def save_fec_data_to_db(fec_data: List[Dict]):
    # ... (no changes to this function)
    if not fec_data: return
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        for item in fec_data:
            cursor.execute(
                "INSERT OR REPLACE INTO fec_candidate_receipts (candidate_name, election_year, party, total_receipts) VALUES (?, ?, ?, ?)",
                (item.get('candidate_name'), item.get('election_year'), item.get('party'), item.get('total_receipts'))
            )
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error during FEC data insertion: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()

def save_turnout_data_to_db(turnout_data: List[Dict]):
    """Saves the detailed turnout statistics to the new database table."""
    if not turnout_data:
        logger.warning("No turnout data provided to save.")
        return

    logger.info(f"Saving {len(turnout_data)} turnout records to the database...")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        for item in turnout_data:
            cursor.execute("""
                INSERT OR REPLACE INTO turnout_statistics (
                    state, year, voting_eligible_population, voting_age_population,
                    prison, probation, parole, total_ineligible_felon, overseas_eligible
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get('state'),
                item.get('year'),
                item.get('voting_eligible_population'),
                item.get('voting_age_population'),
                item.get('prison'),
                item.get('probation'),
                item.get('parole'),
                item.get('total_ineligible_felon'),
                item.get('overseas_eligible')
            ))
        conn.commit()
        logger.info("Successfully saved all turnout data.")
    except sqlite3.Error as e:
        logger.error(f"Database error during turnout data insertion: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()
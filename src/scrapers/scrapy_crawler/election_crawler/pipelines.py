import sqlite3
import logging

class ElectionDbPipeline:
    def __init__(self, db_path='election_data.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.logger = logging.getLogger(__name__)

    def open_spider(self, spider):
        """Called when the spider is opened."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.logger.info(f"Database connection opened for spider: {spider.name}")
        # We assume tables are already created by main.py

    def close_spider(self, spider):
        """Called when the spider is closed."""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.logger.info(f"Database connection closed for spider: {spider.name}")

    def process_item(self, item, spider):
        """
        This method is called for every item yielded by the spider.
        It handles the database insertion logic.
        """
        try:
            # 1. Insert/update state info
            self.cursor.execute(
                "INSERT OR IGNORE INTO states (state_name, electoral_votes) VALUES (?, ?)",
                (item['state_name'], item['electoral_votes'])
            )
            # Update electoral votes in case they changed
            self.cursor.execute(
                "UPDATE states SET electoral_votes = ? WHERE state_name = ?",
                (item['electoral_votes'], item['state_name'])
            )

            # 2. Insert the result data
            self.cursor.execute(
                """INSERT OR REPLACE INTO results (state_name, year, dem_state_percentage, 
                                                 rep_state_percentage, state_winner) 
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    item['state_name'], item['year'],
                    item['dem_state_percentage'], item['rep_state_percentage'],
                    item['state_winner']
                )
            )
        except sqlite3.Error as e:
            self.logger.error(f"Database error processing item for {item.get('state_name')}: {e}")

        return item # Must return the item for other pipelines
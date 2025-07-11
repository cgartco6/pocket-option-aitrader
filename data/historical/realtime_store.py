"""
realtime_store.py - Store real-time market data
"""

import sqlite3
import time
import json
import logging
from config import settings

logger = logging.getLogger(_name_)

class RealTimeStore:
    def _init_(self):
        self.db_file = "data/historical/realtime.db"
        self.create_table()
        
    def create_table(self):
        """Create database table if not exists"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS market_data (
                     timestamp REAL PRIMARY KEY,
                     instrument TEXT,
                     price REAL,
                     volume REAL,
                     source TEXT)''')
        conn.commit()
        conn.close()
        
    def save_tick(self, instrument, price, volume, source="ws"):
        """Save market tick to database"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("INSERT INTO market_data VALUES (?, ?, ?, ?, ?)",
                     (time.time(), instrument, price, volume, source))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving tick: {str(e)}")
            
    def get_recent_ticks(self, instrument, limit=100):
        """Get recent market ticks"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("SELECT timestamp, price, volume FROM market_data "
                      "WHERE instrument = ? ORDER BY timestamp DESC LIMIT ?",
                     (instrument, limit))
            data = c.fetchall()
            conn.close()
            return data
        except Exception as e:
            logger.error(f"Error retrieving ticks: {str(e)}")
            return []

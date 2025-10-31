"""
Database layer for persisting trades and portfolio
"""

import sqlite3
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradeDatabase:
    """SQLite database for trades"""
    
    def __init__(self, db_path='../data/trades.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                coin TEXT NOT NULL,
                type TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                cost_or_revenue REAL,
                pnl REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Portfolio table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coin TEXT UNIQUE NOT NULL,
                capital REAL NOT NULL,
                inventory REAL NOT NULL,
                avg_buy_price REAL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized ✅")
    
    def add_trade(self, coin: str, trade_type: str, price: float, quantity: float, 
                  cost_or_revenue: float, pnl: float = 0):
        """Add trade to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (timestamp, coin, type, price, quantity, cost_or_revenue, pnl)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), coin, trade_type, price, quantity, cost_or_revenue, pnl))
            
            conn.commit()
            conn.close()
            logger.info(f"Trade recorded: {coin} {trade_type} @ {price}")
            return True
        except Exception as e:
            logger.error(f"Error adding trade: {e}")
            return False
    
    def get_all_trades(self, limit: int = 1000):
        """Get all trades"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?', (limit,))
            trades = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return trades
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []
    
    def get_trades_by_coin(self, coin: str):
        """Get trades for specific coin"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM trades WHERE coin = ? ORDER BY timestamp DESC', (coin,))
            trades = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return trades
        except Exception as e:
            logger.error(f"Error fetching trades for {coin}: {e}")
            return []
    
    def clear_all_trades(self):
        """Clear all trades (for testing)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM trades')
            conn.commit()
            conn.close()
            logger.warning("All trades cleared!")
            return True
        except Exception as e:
            logger.error(f"Error clearing trades: {e}")
            return False


if __name__ == "__main__":
    db = TradeDatabase()
    print("Database module loaded ✅")

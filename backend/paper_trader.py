"""
Live Paper Trading Engine - FIXED VERSION
With proper error handling, database persistence, and debugging
"""

import pandas as pd
import numpy as np
from datetime import datetime
import ccxt
from grid_strategy import GridTradingStrategy
from database import TradeDatabase
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperTradingEngine:
    """
    Live paper trading simulator with persistence
    """
    
    def __init__(self, coins_config: dict):
        """
        coins_config: {
            'BTC': {'grid_size': 0.02, 'capital': 25000},
            ...
        }
        """
        self.coins_config = coins_config
        self.db = TradeDatabase()
        
        # Initialize portfolio
        self.portfolio = {}
        for coin, config in coins_config.items():
            self.portfolio[coin] = {
                'capital': config['capital'],
                'inventory': 0,
                'avg_buy_price': 0,
                'current_price': 0,
                'inventory_value': 0,
                'grid_size': config['grid_size']
            }
        
        # Try to initialize exchange
        try:
            self.exchange = ccxt.binance({'enableRateLimit': True})
            logger.info("✅ Connected to Binance")
        except Exception as e:
            logger.error(f"❌ Exchange error: {e}")
            self.exchange = None
        
        self.trading_active = False
        self.last_update = datetime.now()
        logger.info("Paper Trading Engine Initialized ✅")
    
    def fetch_current_price(self, symbol: str) -> float:
        """Fetch current price from exchange"""
        try:
            if not self.exchange:
                logger.warning(f"⚠️  No exchange connection for {symbol}")
                return None
            
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            logger.debug(f"Fetched {symbol}: ${price:.2f}")
            return price
        
        except ccxt.NetworkError as e:
            logger.error(f"❌ Network error fetching {symbol}: {e}")
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"❌ Exchange error fetching {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching {symbol}: {e}")
            return None
    
    def execute_buy(self, coin: str, price: float) -> bool:
        """Execute buy order"""
        try:
            portfolio = self.portfolio[coin]
            
            # Calculate order
            order_amount = portfolio['capital'] * 0.1  # 10% per order
            coins_to_buy = order_amount / price
            
            # Include fees (0.6%)
            total_cost = order_amount * 1.006
            
            # Check if we have enough capital
            if portfolio['capital'] < total_cost:
                logger.warning(f"⚠️  Insufficient capital for {coin} buy")
                return False
            
            # Execute
            portfolio['capital'] -= total_cost
            old_inventory = portfolio['inventory']
            portfolio['inventory'] += coins_to_buy
            
            # Update avg buy price
            if old_inventory > 0:
                portfolio['avg_buy_price'] = (
                    (portfolio['avg_buy_price'] * old_inventory + price * coins_to_buy) / 
                    portfolio['inventory']
                )
            else:
                portfolio['avg_buy_price'] = price
            
            # Log trade
            self.db.add_trade(
                coin=coin,
                trade_type='BUY',
                price=price,
                quantity=coins_to_buy,
                cost_or_revenue=total_cost,
                pnl=0
            )
            
            logger.info(f"✅ BUY {coin}: {coins_to_buy:.6f} @ ${price:.2f}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error buying {coin}: {e}")
            return False
    
    def execute_sell(self, coin: str, price: float) -> bool:
        """Execute sell order"""
        try:
            portfolio = self.portfolio[coin]
            
            # Check if we have inventory
            if portfolio['inventory'] <= 0:
                return False
            
            # Sell 50% of inventory
            coins_to_sell = portfolio['inventory'] * 0.5
            
            # Calculate revenue
            gross_revenue = coins_to_sell * price
            
            # Deduct fees
            trade_fee = gross_revenue * 0.006
            tds = gross_revenue * 0.01
            
            # Calculate gains
            gross_gain = gross_revenue - (coins_to_sell * portfolio['avg_buy_price'])
            tax = max(0, gross_gain * 0.30)
            
            # Net proceeds
            net_proceeds = gross_revenue - trade_fee - tds - tax
            
            # Execute
            portfolio['capital'] += net_proceeds
            portfolio['inventory'] -= coins_to_sell
            
            pnl = net_proceeds - (coins_to_sell * portfolio['avg_buy_price'])
            
            # Log trade
            self.db.add_trade(
                coin=coin,
                trade_type='SELL',
                price=price,
                quantity=coins_to_sell,
                cost_or_revenue=net_proceeds,
                pnl=pnl
            )
            
            logger.info(f"✅ SELL {coin}: {coins_to_sell:.6f} @ ${price:.2f} | P&L: ₹{pnl:.2f}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error selling {coin}: {e}")
            return False
    
    def update_portfolio_values(self):
        """Update current prices and inventory values"""
        try:
            for coin in self.portfolio.keys():
                price = self.fetch_current_price(f'{coin}/USDT')
                
                if price is None:
                    logger.warning(f"⚠️  Could not fetch price for {coin}")
                    continue
                
                portfolio = self.portfolio[coin]
                portfolio['current_price'] = price
                portfolio['inventory_value'] = portfolio['inventory'] * price
            
            self.last_update = datetime.now()
            logger.debug("Portfolio values updated ✅")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error updating portfolio: {e}")
            return False
    
    def execute_grid_trading_cycle(self):
        """Execute one grid trading cycle for all coins"""
        try:
            logger.info("=" * 50)
            logger.info("GRID TRADING CYCLE START")
            logger.info("=" * 50)
            
            # Update prices first
            self.update_portfolio_values()
            
            for coin in self.portfolio.keys():
                portfolio = self.portfolio[coin]
                price = portfolio['current_price']
                
                if price == 0:
                    logger.warning(f"⚠️  No price for {coin}, skipping")
                    continue
                
                grid_size = portfolio['grid_size']
                
                # Calculate grid levels
                buy_levels = [price * (1 - grid_size * j) for j in range(1, 11)]
                sell_levels = [price * (1 + grid_size * j) for j in range(1, 11)]
                
                # Buy at lowest available level
                if portfolio['inventory'] < 1:  # Only buy if we have room
                    self.execute_buy(coin, buy_levels[0])
                
                # Sell if we have inventory
                if portfolio['inventory'] > 0:
                    self.execute_sell(coin, sell_levels[0])
            
            logger.info("GRID TRADING CYCLE END ✅")
            logger.info("=" * 50)
            return True
        
        except Exception as e:
            logger.error(f"❌ Grid trading cycle failed: {e}")
            return False
    
    def get_status(self):
        """Get current status for UI"""
        try:
            total_value = 0
            
            for coin, portfolio in self.portfolio.items():
                total_value += portfolio['capital'] + portfolio['inventory_value']
            
            return {
                'timestamp': datetime.now().isoformat(),
                'portfolio': self.portfolio,
                'total_value': total_value,
                'trading_active': self.trading_active,
                'last_update': self.last_update.isoformat(),
                'num_trades': len(self.db.get_all_trades())
            }
        
        except Exception as e:
            logger.error(f"❌ Error getting status: {e}")
            return None
    
    def get_recent_trades(self, limit: int = 100):
        """Get recent trades from database"""
        try:
            return self.db.get_all_trades(limit)
        except Exception as e:
            logger.error(f"❌ Error fetching trades: {e}")
            return []


if __name__ == "__main__":
    print("Paper Trading Engine loaded ✅")

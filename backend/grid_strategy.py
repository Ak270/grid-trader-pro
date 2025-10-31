"""
Grid Trading Strategy - EXACT COPY OF WORKING VERSION
NO MODIFICATIONS
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GridTradingStrategy:
    """
    Grid trading implementation
    """
    
    def __init__(
        self,
        grid_size: float = 0.02,  # 2% grid spacing
        grids_count: int = 10,     # Number of buy/sell levels
        initial_capital: float = 100000
    ):
        self.grid_size = grid_size
        self.grids_count = grids_count
        self.initial_capital = initial_capital
        
        logger.info(f"Grid Trading Strategy")
        logger.info(f"  Grid Size: {grid_size*100}%")
        logger.info(f"  Number of Grids: {grids_count}")
    
    def backtest(self, data: pd.DataFrame) -> Dict:
        """
        Simulate grid trading
        """
        
        logger.info(f"Backtesting on {len(data)} candles")
        
        # Trading variables
        capital = self.initial_capital
        inventory = 0  # Number of coins held
        avg_buy_price = 0
        
        trades = []
        balance_history = [capital]
        
        for i in range(len(data)):
            current = data.iloc[i]
            price = current['close']
            
            # Calculate grid levels based on current price
            base_price = price
            
            # Buy levels (below current price)
            buy_levels = [base_price * (1 - self.grid_size * j) for j in range(1, self.grids_count + 1)]
            
            # Sell levels (above current price)
            sell_levels = [base_price * (1 + self.grid_size * j) for j in range(1, self.grids_count + 1)]
            
            # Check if price hits any buy level
            for buy_level in buy_levels:
                if current['low'] <= buy_level <= current['high']:
                    # Buy at this level
                    coins_to_buy = (capital * 0.1) / buy_level  # Use 10% of capital per buy
                    
                    if coins_to_buy > 0:
                        # Execute buy
                        buy_cost = coins_to_buy * buy_level
                        trade_cost = buy_cost * 0.006  # 0.6% trading cost
                        total_cost = buy_cost + trade_cost
                        
                        if capital >= total_cost:
                            capital -= total_cost
                            inventory += coins_to_buy
                            avg_buy_price = (avg_buy_price * (inventory - coins_to_buy) + buy_level * coins_to_buy) / inventory if inventory > 0 else buy_level
                            
                            trades.append({
                                'date': current.name,
                                'type': 'BUY',
                                'price': buy_level,
                                'quantity': coins_to_buy,
                                'cost': total_cost
                            })
                    break
            
            # Check if price hits any sell level
            for sell_level in sell_levels:
                if current['low'] <= sell_level <= current['high']:
                    if inventory > 0:
                        # Sell at this level
                        coins_to_sell = inventory * 0.5  # Sell 50% of inventory
                        
                        sell_revenue = coins_to_sell * sell_level
                        trade_cost = sell_revenue * 0.006
                        tds = sell_revenue * 0.01
                        
                        # Calculate tax (30% on gains only)
                        gross_gain = sell_revenue - (coins_to_sell * avg_buy_price)
                        tax = max(0, gross_gain * 0.30)
                        
                        net_proceeds = sell_revenue - trade_cost - tds - tax
                        
                        capital += net_proceeds
                        inventory -= coins_to_sell
                        
                        trades.append({
                            'date': current.name,
                            'type': 'SELL',
                            'price': sell_level,
                            'quantity': coins_to_sell,
                            'revenue': net_proceeds,
                            'gain': gross_gain,
                            'tax': tax
                        })
                    break
            
            # Update balance (coins at current price + cash)
            current_inventory_value = inventory * price
            total_balance = capital + current_inventory_value
            balance_history.append(total_balance)
        
        # Final balance (convert remaining coins to cash at last price)
        final_price = data.iloc[-1]['close']
        final_inventory_value = inventory * final_price
        final_balance = capital + final_inventory_value
        
        # Calculate metrics
        trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
        
        total_return = ((final_balance - self.initial_capital) / self.initial_capital) * 100
        
        # Calculate win rate from sell trades
        sell_trades = [t for t in trades if t['type'] == 'SELL']
        winning_sells = len([t for t in sell_trades if t.get('gain', 0) > 0])
        
        win_rate = (winning_sells / len(sell_trades) * 100) if sell_trades else 0
        
        # Sharpe ratio
        returns = np.diff(balance_history) / balance_history[:-1]
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
        else:
            sharpe = 0
        
        # Max drawdown
        peak = np.maximum.accumulate(balance_history)
        drawdown = (np.array(balance_history) - peak) / peak * 100
        max_drawdown = np.min(drawdown)
        
        return {
            'final_capital': final_balance,
            'total_return_pct': total_return,
            'profit_loss': final_balance - self.initial_capital,
            'num_trades': len(trades),
            'num_buy_trades': len([t for t in trades if t['type'] == 'BUY']),
            'num_sell_trades': len(sell_trades),
            'win_rate_pct': win_rate,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_drawdown,
            'trades_per_month': len(trades) / (len(data) / (24 * 30)),
            'trades': trades_df,
            'inventory_remaining': inventory,
            'final_price': final_price
        }


if __name__ == "__main__":
    print("Grid Trading Strategy loaded ✅")

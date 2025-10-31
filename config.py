"""
Configuration for Grid Trader Pro
"""

# Paper Trading Config
PAPER_TRADING_CONFIG = {
    'BTC': {
        'grid_size': 0.02,
        'grids_count': 10,
        'initial_capital': 25000
    },
    'ETH': {
        'grid_size': 0.025,
        'grids_count': 10,
        'initial_capital': 25000
    },
    'SOL': {
        'grid_size': 0.025,
        'grids_count': 10,
        'initial_capital': 25000
    },
    'BNB': {
        'grid_size': 0.03,
        'grids_count': 10,
        'initial_capital': 25000
    }
}

# Flask Config
FLASK_ENV = 'development'
DEBUG = True
PORT = 5000

# Exchange Config
EXCHANGE = 'binance'
TIMEFRAME = '4h'

# Update frequency (seconds)
UPDATE_INTERVAL = 5

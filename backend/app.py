"""
Flask Web App - Grid Trading Paper Trader UI (ENHANCED)
With pagination, better caching, and detailed metrics
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
from datetime import datetime, timedelta
from paper_trader import PaperTradingEngine
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
CORS(app)

# Initialize paper trading engine
coins_config = {
    'BTC': {'grid_size': 0.02, 'capital': 25000},
    'ETH': {'grid_size': 0.025, 'capital': 25000},
    'SOL': {'grid_size': 0.025, 'capital': 25000},
    'BNB': {'grid_size': 0.03, 'capital': 25000}
}

engine = PaperTradingEngine(coins_config)

# Global state
trading_thread = None
trading_active = False
TRADING_INTERVAL = 60

# Price cache (to avoid hammering exchange)
price_cache = {}
last_price_fetch = {}
PRICE_CACHE_TTL = 30  # seconds


def run_trading_loop():
    """Main trading loop"""
    global trading_active
    
    logger.info("🚀 TRADING LOOP STARTED")
    
    while trading_active:
        try:
            logger.info("Executing grid trading cycle...")
            engine.execute_grid_trading_cycle()
            time.sleep(TRADING_INTERVAL)
        
        except Exception as e:
            logger.error(f"❌ Error in trading loop: {e}")
            time.sleep(5)
    
    logger.info("🛑 TRADING LOOP STOPPED")


@app.route('/')
def index():
    """Dashboard page"""
    return render_template('index.html')


@app.route('/api/status')
def status():
    """Get current status"""
    try:
        status_data = engine.get_status()
        return jsonify(status_data) if status_data else jsonify({'error': 'Failed'}), 500
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard')
def dashboard():
    """Get dashboard data with metrics"""
    try:
        status_data = engine.get_status()
        
        if status_data is None:
            return jsonify({'error': 'Failed'}), 500
        
        # Calculate totals
        total_capital = sum([p['capital'] for p in engine.portfolio.values()])
        total_inventory_value = sum([p.get('inventory_value', 0) for p in engine.portfolio.values()])
        total_value = total_capital + total_inventory_value
        
        # Net P&L (AFTER tax and fees - already deducted in trades)
        net_pnl = total_value - 100000
        net_pnl_pct = (net_pnl / 100000) * 100
        
        # Get all trades
        all_trades = engine.get_recent_trades(limit=10000)
        
        # Calculate metrics
        buy_trades = [t for t in all_trades if t['type'] == 'BUY']
        sell_trades = [t for t in all_trades if t['type'] == 'SELL']
        winning_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
        
        win_rate = (len(winning_trades) / len(sell_trades) * 100) if sell_trades else 0
        
        # Calculate returns
        if sell_trades:
            total_sell_revenue = sum([t.get('cost_or_revenue', 0) for t in sell_trades])
            avg_trade_size = total_sell_revenue / len(sell_trades) if sell_trades else 0
        else:
            avg_trade_size = 0
        
        # Start time (first trade or now if no trades)
        if all_trades:
            start_time = datetime.fromisoformat(all_trades[-1]['created_at'])
            trading_days = (datetime.now() - start_time).days + 1
        else:
            trading_days = 1
        
        daily_return = (net_pnl / 100000) / trading_days * 100 if trading_days > 0 else 0
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'total_capital': total_capital,
            'total_inventory_value': total_inventory_value,
            'total_portfolio_value': total_value,
            'net_pnl': net_pnl,
            'net_pnl_pct': net_pnl_pct,
            'num_trades': status_data['num_trades'],
            'num_buy_trades': len(buy_trades),
            'num_sell_trades': len(sell_trades),
            'win_rate_pct': win_rate,
            'avg_trade_size': avg_trade_size,
            'daily_return_pct': daily_return,
            'portfolio': engine.portfolio,
            'trading_active': trading_active,
            'last_update': status_data['last_update'],
            'trading_days': trading_days
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/trades')
def trades():
    """Get paginated trades"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 15
        
        all_trades = engine.get_recent_trades(limit=10000)
        
        # Reverse to show newest first
        all_trades = all_trades[::-1]
        
        # Paginate
        total_trades = len(all_trades)
        total_pages = (total_trades + per_page - 1) // per_page
        
        start = (page - 1) * per_page
        end = start + per_page
        
        paginated_trades = all_trades[start:end]
        
        return jsonify({
            'trades': paginated_trades,
            'page': page,
            'per_page': per_page,
            'total_trades': total_trades,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio')
def portfolio():
    """Get current portfolio"""
    try:
        portfolio_data = []
        
        for coin, data in engine.portfolio.items():
            total_value = data['capital'] + data['inventory_value']
            pnl = total_value - 25000
            pnl_pct = (pnl / 25000 * 100) if 25000 > 0 else 0
            
            portfolio_data.append({
                'coin': coin,
                'capital': round(data['capital'], 2),
                'inventory': round(data['inventory'], 6),
                'current_price': round(data['current_price'], 2),
                'inventory_value': round(data['inventory_value'], 2),
                'total_value': round(total_value, 2),
                'pnl': round(pnl, 2),
                'pnl_pct': round(pnl_pct, 2)
            })
        
        return jsonify(portfolio_data)
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/prices')
def prices():
    """Get current prices (cached to reduce load)"""
    try:
        prices_data = {}
        current_time = time.time()
        
        for coin in engine.portfolio.keys():
            # Check cache
            if coin in price_cache and coin in last_price_fetch:
                if current_time - last_price_fetch[coin] < PRICE_CACHE_TTL:
                    prices_data[coin] = price_cache[coin]
                    continue
            
            # Fetch from engine
            price = engine.portfolio[coin].get('current_price', 0)
            prices_data[coin] = price
            
            # Update cache
            price_cache[coin] = price
            last_price_fetch[coin] = current_time
        
        return jsonify(prices_data)
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def stats():
    """Get detailed statistics"""
    try:
        all_trades = engine.get_recent_trades(limit=10000)
        
        if not all_trades:
            return jsonify({
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'total_loss': 0,
                'avg_profit_per_trade': 0
            })
        
        buy_trades = [t for t in all_trades if t['type'] == 'BUY']
        sell_trades = [t for t in all_trades if t['type'] == 'SELL']
        
        profits = [t.get('pnl', 0) for t in sell_trades if t.get('pnl', 0) > 0]
        losses = [t.get('pnl', 0) for t in sell_trades if t.get('pnl', 0) < 0]
        
        total_profit = sum(profits)
        total_loss = sum(losses)
        
        winning_trades = len(profits)
        win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0
        
        avg_profit = (total_profit / len(profits)) if profits else 0
        avg_loss = (total_loss / len(losses)) if losses else 0
        
        return jsonify({
            'total_trades': len(all_trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'winning_trades': winning_trades,
            'losing_trades': len(losses),
            'win_rate_pct': win_rate,
            'total_profit': round(total_profit, 2),
            'total_loss': round(total_loss, 2),
            'avg_profit_per_trade': round(avg_profit, 2),
            'avg_loss_per_trade': round(avg_loss, 2),
            'profit_factor': abs(total_profit / total_loss) if total_loss != 0 else 0
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/start-trading', methods=['POST'])
def start_trading():
    """Start paper trading"""
    global trading_active, trading_thread
    
    try:
        if trading_active:
            return jsonify({'error': 'Trading already active'}), 400
        
        trading_active = True
        logger.info("✅ Trading started")
        
        trading_thread = threading.Thread(target=run_trading_loop, daemon=True)
        trading_thread.start()
        
        return jsonify({'status': 'started'})
    
    except Exception as e:
        logger.error(f"Error: {e}")
        trading_active = False
        return jsonify({'error': str(e)}), 500


@app.route('/api/stop-trading', methods=['POST'])
def stop_trading():
    """Stop paper trading"""
    global trading_active
    
    try:
        trading_active = False
        logger.info("🛑 Trading stopped")
        return jsonify({'status': 'stopped'})
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export-trades')
def export_trades():
    """Export trades to CSV"""
    try:
        trades_list = engine.get_recent_trades(limit=10000)
        
        if not trades_list:
            return jsonify({'error': 'No trades'}), 400
        
        df = pd.DataFrame(trades_list)
        csv = df.to_csv(index=False)
        
        return csv, 200, {'Content-Disposition': 'attachment; filename=trades.csv'}
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Error: {e}")
    return jsonify({'error': 'Internal error'}), 500


if __name__ == '__main__':
    logger.info("Starting Grid Trader Pro...")
    app.run(debug=True, port=5000, use_reloader=False)

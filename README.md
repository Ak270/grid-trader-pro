# Grid Trader Pro 📈

**Professional Grid Trading Paper Trader with Live Web Dashboard**

A free, open-source grid trading simulator for crypto (BTC, ETH, SOL, BNB). Test strategies without risking real money, track performance with beautiful real-time UI.

## ✨ Features

- ✅ **Live Paper Trading**: Simulate grid trading without real capital
- ✅ **Real-time Dashboard**: Beautiful web UI with live updates
- ✅ **Multi-Coin Support**: Trade BTC, ETH, SOL, BNB simultaneously
- ✅ **Detailed Analytics**: Win rate, profit factor, Sharpe ratio, drawdown
- ✅ **Trade History**: Paginated (15 per page) with export to CSV
- ✅ **Performance Metrics**: Daily returns, P&L tracking, cost breakdown
- ✅ **100% Free**: MIT Licensed, open-source
- ✅ **Easy to Deploy**: Local, GitHub, Replit, or VPS

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip (Python package manager)

### Installation

Clone repository
git clone https://github.com/YOUR_USERNAME/grid-trader-pro.git
cd grid_trader_pro
Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate  # Windows
Install dependencies
pip install -r requirements.txt
Run the app
cd backend
python app.py

### Open in Browser
http://localhost:5000

### Start Trading
1. Click **Start** button
2. Watch grid trading execute in real-time
3. Monitor portfolio and trades on dashboard
4. Click **Stop** when done
5. Export trades to CSV

## 📊 Dashboard Sections

### Key Metrics
- **Total P&L**: Net profit/loss after all taxes & fees
- **Portfolio Value**: Current total capital
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Ratio of wins to losses

### Performance Metrics
- Buy/Sell trades count
- Winning/Losing trades
- Average win/loss
- Profit factor

### Portfolio Status
- Real-time prices (cached every 30s)
- Current inventory per coin
- Unrealized P&L
- Individual coin performance

### Trade History
- 15 trades per page (paginated)
- Entry/exit details
- P&L per trade
- Type (BUY/SELL)
- Export to CSV

## ⚙️ Configuration

Edit `config.py` to adjust:

PAPER_TRADING_CONFIG = {
‘BTC’: {‘grid_size’: 0.02, ‘capital’: 25000},
‘ETH’: {‘grid_size’: 0.025, ‘capital’: 25000},
‘SOL’: {‘grid_size’: 0.025, ‘capital’: 25000},
‘BNB’: {‘grid_size’: 0.03, ‘capital’: 25000}
}

## 🔄 Reset Database

Start fresh with new ₹1,00,000:


rm -f data/trades.db
python app.py

## 📤 Deployment

### Local Machine (Recommended for testing)

cd backend
python app.py
Open http://localhost:5000

### "Database locked" errors
- Close all other instances of the app
- Delete `data/trades.db` and restart

## 🤝 Contributing

Want to improve Grid Trader Pro?

1. Fork the repository
2. Create a branch: `git checkout -b feature/YourFeature`
3. Make changes
4. Commit: `git commit -m "Add YourFeature"`
5. Push: `git push origin feature/YourFeature`
6. Submit pull request

## 📝 License

MIT License - Free to use, modify, distribute
See `LICENSE` file for details

## 💬 Support

- Issues? Open a GitHub issue
- Questions? Check existing issues first
- Want to contribute? See Contributing section

## ⚠️ Disclaimer

- **Paper Trading Only**: This is a simulator, not real trading
- **No Real Capital at Risk**: All trading is simulated
- **Educational Purpose**: Use to learn trading strategies
- **Not Financial Advice**: Do your own research before live trading
- **Past Performance ≠ Future Results**

## 🎯 Roadmap

- [ ] Live trading integration (Binance API)
- [ ] Advanced charting with TradingView
- [ ] Machine learning strategy optimization
- [ ] Multi-exchange support
- [ ] Portfolio backtesting tool
- [ ] Risk metrics dashboard

## 📞 Contact

Your Name - [@YourTwitter](https://twitter.com) - your.email@example.com

Project Link: [https://github.com/YOUR_USERNAME/grid-trader-pro](https://github.com/YOUR_USERNAME/grid-trader-pro)

---

**Made with ❤️ by Traders, for Traders**

⭐ If this helped you, please star the repository! ⭐

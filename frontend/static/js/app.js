// Grid Trader Pro - Enhanced Frontend Logic

let updateInterval;
let tradingActive = false;
let currentPage = 1;
let totalPages = 1;
let priceCache = {};
let lastPriceFetch = 0;

async function fetchDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // Update main metrics
        const pnl = data.net_pnl;
        const pnlPercent = data.net_pnl_pct.toFixed(2);
        
        document.getElementById('netPnL').textContent = `₹${pnl.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
        document.getElementById('netPnL').className = pnl >= 0 ? 'text-success' : 'text-danger';
        
        document.getElementById('pnlPct').textContent = `${pnlPercent}% return`;
        document.getElementById('portfolioValue').textContent = 
            `₹${data.total_portfolio_value.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
        document.getElementById('dailyReturn').textContent = `${data.daily_return_pct.toFixed(2)}% daily`;
        document.getElementById('winRate').textContent = `${data.win_rate_pct.toFixed(1)}%`;
        document.getElementById('totalTrades').textContent = `${data.num_trades} trades`;
        document.getElementById('tradingDays').textContent = `${data.trading_days} days`;
        
        // Update status
        document.getElementById('status').textContent = data.trading_active ? '🟢 Live' : '⚪ Paused';
        document.getElementById('status').className = 
            data.trading_active ? 'badge bg-success' : 'badge bg-secondary';
        
        tradingActive = data.trading_active;
        updateButtonStates();
        
        // Fetch additional stats
        fetchStats();
        updatePortfolioTable(data.portfolio);
        updateTradesTable(currentPage);
        
    } catch (error) {
        console.error('Dashboard error:', error);
        showError(`Error: ${error.message}`);
    }
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const stats = await response.json();
        
        document.getElementById('buyTrades').textContent = stats.buy_trades;
        document.getElementById('sellTrades').textContent = stats.sell_trades;
        document.getElementById('winningTrades').textContent = stats.winning_trades;
        document.getElementById('losingTrades').textContent = stats.losing_trades;
        document.getElementById('avgWin').textContent = `₹${stats.avg_profit_per_trade.toFixed(0)}`;
        document.getElementById('avgLoss').textContent = `₹${Math.abs(stats.avg_loss_per_trade).toFixed(0)}`;
        document.getElementById('profitFactor').textContent = stats.profit_factor.toFixed(2);
        
    } catch (error) {
        console.error('Stats error:', error);
    }
}

function updateButtonStates() {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    startBtn.disabled = tradingActive;
    stopBtn.disabled = !tradingActive;
}

async function updatePortfolioTable(portfolio) {
    try {
        const tbody = document.getElementById('portfolioBody');
        tbody.innerHTML = '';
        
        for (const [coin, data] of Object.entries(portfolio)) {
            const totalValue = data.capital + (data.inventory_value || 0);
            const pnlPct = ((totalValue - 25000) / 25000 * 100).toFixed(2);
            
            // Fetch latest price
            const price = await getPriceEfficiently(coin);
            
            const row = `
                <tr>
                    <td><strong>${coin}</strong></td>
                    <td>₹${data.capital.toLocaleString('en-IN', {maximumFractionDigits: 0})}</td>
                    <td>${data.inventory.toFixed(6)}</td>
                    <td id="price_${coin}">₹${(price || data.current_price || 0).toLocaleString('en-IN', {maximumFractionDigits: 2})}</td>
                    <td>₹${(data.inventory_value || 0).toLocaleString('en-IN', {maximumFractionDigits: 0})}</td>
                    <td><strong>₹${totalValue.toLocaleString('en-IN', {maximumFractionDigits: 0})}</strong></td>
                    <td><span class="badge ${pnlPct >= 0 ? 'bg-success' : 'bg-danger'}">${pnlPct}%</span></td>
                </tr>
            `;
            tbody.innerHTML += row;
        }
    } catch (error) {
        console.error('Portfolio error:', error);
    }
}

async function getPriceEfficiently(coin) {
    /**
     * Get price from cache or fetch if cache expired
     * Reduces server/GitHub load significantly
     */
    try {
        const currentTime = Date.now();
        
        // Check if cache is fresh (30 second TTL)
        if (priceCache[coin] && (currentTime - lastPriceFetch) < 30000) {
            return priceCache[coin];
        }
        
        // Fetch fresh prices
        if (currentTime - lastPriceFetch > 30000) {
            const response = await fetch('/api/prices');
            if (!response.ok) return null;
            
            const prices = await response.json();
            priceCache = prices;
            lastPriceFetch = currentTime;
            
            return priceCache[coin] || null;
        }
        
        return priceCache[coin] || null;
        
    } catch (error) {
        console.error('Price fetch error:', error);
        return null;
    }
}

async function updateTradesTable(page = 1) {
    try {
        const response = await fetch(`/api/trades?page=${page}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        const tbody = document.getElementById('tradesBody');
        tbody.innerHTML = '';
        
        if (data.trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No trades yet</td></tr>';
        } else {
            data.trades.forEach(trade => {
                const timestamp = new Date(trade.timestamp).toLocaleString();
                const row = `
                    <tr>
                        <td>${timestamp}</td>
                        <td><strong>${trade.coin}</strong></td>
                        <td><span class="badge ${trade.type === 'BUY' ? 'bg-primary' : 'bg-success'}">${trade.type}</span></td>
                        <td>₹${parseFloat(trade.price).toFixed(2)}</td>
                        <td>${parseFloat(trade.quantity).toFixed(6)}</td>
                        <td>₹${(parseFloat(trade.cost_or_revenue) || 0).toFixed(2)}</td>
                        <td>${trade.pnl ? `₹${parseFloat(trade.pnl).toFixed(2)}` : '-'}</td>
                    </tr>
                `;
                tbody.innerHTML += row;
            });
        }
        
        // Update pagination
        updatePagination(data.page, data.total_pages, data.total_trades);
        currentPage = data.page;
        totalPages = data.total_pages;
        
    } catch (error) {
        console.error('Trades error:', error);
    }
}

function updatePagination(page, totalPages, totalTrades) {
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';
    
    // Previous button
    if (page > 1) {
        controls.innerHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="goToPage(${page - 1})">Previous</a>
            </li>
        `;
    }
    
    // Page numbers
    for (let i = Math.max(1, page - 2); i <= Math.min(totalPages, page + 2); i++) {
        controls.innerHTML += `
            <li class="page-item ${i === page ? 'active' : ''}">
                <a class="page-link" href="#" onclick="goToPage(${i})">${i}</a>
            </li>
        `;
    }
    
    // Next button
    if (page < totalPages) {
        controls.innerHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="goToPage(${page + 1})">Next</a>
            </li>
        `;
    }
    
    // Add info
    controls.innerHTML += `<li class="page-item disabled"><span class="page-link">${totalTrades} total trades</span></li>`;
}

function goToPage(page) {
    currentPage = page;
    updateTradesTable(page);
}

async function startTrading() {
    try {
        const response = await fetch('/api/start-trading', {method: 'POST'});
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        tradingActive = true;
        updateButtonStates();
        
        // Update frequently when trading
        if (updateInterval) clearInterval(updateInterval);
        updateInterval = setInterval(fetchDashboard, 5000);  // Every 5 seconds
        
        fetchDashboard();
        showNotification('Trading started! 🚀');
        
    } catch (error) {
        console.error('Start error:', error);
        showError(`Failed: ${error.message}`);
    }
}

async function stopTrading() {
    try {
        const response = await fetch('/api/stop-trading', {method: 'POST'});
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        tradingActive = false;
        updateButtonStates();
        
        clearInterval(updateInterval);
        
        showNotification('Trading stopped ⏸️');
        
    } catch (error) {
        console.error('Stop error:', error);
        showError(`Failed: ${error.message}`);
    }
}

async function exportTrades() {
    try {
        const response = await fetch('/api/export-trades');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trades_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showNotification('Trades exported! 📥');
        
    } catch (error) {
        console.error('Export error:', error);
        showError(`Failed: ${error.message}`);
    }
}

function showError(message) {
    console.error(message);
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show fixed-top mt-2';
    alertDiv.innerHTML = `${message} <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}

function showNotification(message) {
    console.log(message);
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    fetchDashboard();
    
    // Update dashboard every 30 seconds when not trading
    setInterval(() => {
        if (!tradingActive) {
            fetchDashboard();
        }
    }, 30000);
    
    // Update prices every 30 seconds
    setInterval(() => {
        if (tradingActive) {
            updatePortfolioTable(document.querySelector('#portfolioTable tbody').dataset.portfolio || {});
        }
    }, 30000);
});

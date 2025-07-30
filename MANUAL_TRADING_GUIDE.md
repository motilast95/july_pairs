# 📊 Manual Trading Guide
## Pairs Trading Strategy - IBKR Paper Trading

---

## 🎯 Overview

This guide covers the **manual operation** of your pairs trading system. The system is designed to run in two phases each trading day:

1. **Evening (5:00 PM)**: Generate trading signals
2. **Morning (9:30 AM)**: Execute trades based on yesterday's signals

---

## 📋 Prerequisites

### ✅ Before Starting Daily Trading:

1. **TWS (Trader Workstation) Running**
   ```bash
   # Make sure TWS is:
   # - Connected to paper trading account
   # - API connections enabled
   # - Running in background
   ```

2. **Python Environment Activated**
   ```bash
   .venv\Scripts\activate
   ```

3. **Initial Training Completed** (One-time setup)
   ```bash
   python -m src.trading.live_trading_setup
   ```

---

## 🕐 Daily Trading Schedule

### **Phase 1: Evening Signal Generation (5:00 PM)**

**Purpose**: Get today's closing prices and generate trading signals

**Command**:
```bash
python -m src.trading.daily_signal_generator
```

**What Happens**:
- Connects to IBKR
- Retrieves today's closing prices for all pairs
- Calculates spreads and z-scores
- Generates signals (LONG/SHORT/HOLD/FLAT)
- Saves signals to `results/live_trading/signals/signals_YYYYMMDD.json`

**Expected Output**:
```
📊 SIGNAL GENERATION SUMMARY
==================================================
📈 JPM-GS: HOLD (z=-0.92)
📈 WFC-C: LONG (z=-4.19)
📈 BAC-AXP: SHORT (z=1.98)
📈 MPC-VLO: HOLD (z=1.18)
✅ Signals saved to: results/live_trading/signals/signals_20250730.json
```

---

### **Phase 2: Morning Trade Execution (9:30 AM)**

**Purpose**: Execute trades based on yesterday's signals

**Command**:
```bash
python -m src.trading.daily_executor
```

**What Happens**:
- Loads yesterday's signals
- Gets current portfolio positions from IBKR
- Calculates required trades (buy/sell based on target vs current positions)
- Executes market orders
- Saves execution results to `results/live_trading/executions/execution_YYYYMMDD.json`

**Expected Output**:
```
📊 DAILY EXECUTION SUMMARY
==================================================
📈 BUY 604 WFC @ $82.35 (Commission: $3.03) (WFC-C)
📈 SELL 524 C @ $95.81 (Commission: $2.59) (WFC-C)
📈 SELL 1036 BAC @ $48.36 (Commission: $5.37) (BAC-AXP)
📈 BUY 163 AXP @ $306.48 (Commission: $1.00) (BAC-AXP)
💰 Total trade value: $199,998.80
💸 Total commission: $12.01
📊 Commission rate: 0.6 bps
📊 Total trades: 4
```

---

## 🛠️ Additional Commands

### **Quick Start Menu**
```bash
python start_live_trading.py
```
Provides a menu interface for all operations.

### **Test IBKR Connection**
```bash
python -m src.trading.ibkr_connection
```
Verifies connection to IBKR and shows account status.

### **View Latest Signals**
```bash
python -m src.trading.daily_signal_generator --view-only
```
Shows the most recent signals without generating new ones.

### **Analyze Transaction Costs**
```bash
python -m src.trading.transaction_cost_analyzer
```
Analyzes historical transaction costs and generates reports.

---

## 🧹 Cleanup Operations

### **After Testing (Clean Slate)**
```bash
python cleanup_live_trading.py
```
Deletes all logs, signals, and execution files.

### **Manual Position Closing**
In TWS:
1. Go to **Account** → **Positions**
2. Select all positions
3. Right-click → **Close All Positions**

---

## 📊 Monitoring & Analysis

### **Check Current Positions**
In TWS:
- **Account** → **Positions** tab
- Shows all current holdings and P&L

### **View Execution History**
```bash
# Check latest execution results
dir results\live_trading\executions

# View specific execution file
type results\live_trading\executions\execution_YYYYMMDD.json
```

### **Review Signal History**
```bash
# Check latest signals
dir results\live_trading\signals

# View specific signal file
type results\live_trading\signals\signals_YYYYMMDD.json
```

---

## ⚠️ Troubleshooting

### **Common Issues & Solutions**

#### **1. TWS Connection Failed**
```
❌ Error: Could not connect to IBKR
```
**Solution**:
- Ensure TWS is running
- Check API connections are enabled
- Verify paper trading account is active

#### **2. No Signal File Found**
```
❌ Error: No signal file found for YYYYMMDD
```
**Solution**:
- Run signal generation first
- Check if signal file exists: `dir results\live_trading\signals`

#### **3. Module Not Found**
```
❌ ModuleNotFoundError: No module named 'pandas'
```
**Solution**:
```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

#### **4. No Trades Executed**
```
📊 No trades to execute
```
**Solution**:
- Check if signals were generated
- Verify current positions match target positions
- Review signal logic

---

## 🔄 Stateful Logic Explanation

### **How the System Handles Consecutive Signals**

**Example Scenario**:
- Day 1: LONG signal → Enter position
- Day 2: LONG signal → **Hold position** (not double up)
- Day 3: FLAT signal → Exit position

**Key Behavior**:
- **Enter**: Only when no position exists
- **Hold**: When already in position and signal is same direction
- **Exit**: Only when signal is FLAT or opposite direction

---

## 📈 Performance Tracking

### **Daily Metrics to Monitor**:
1. **Signal Quality**: Are signals reasonable?
2. **Execution Success**: All orders filled?
3. **Transaction Costs**: Commission rates
4. **Position Sizing**: Dollar allocations per pair
5. **P&L**: Unrealized gains/losses in TWS

### **Weekly Review**:
1. **Transaction Cost Analysis**: Run the analyzer
2. **Signal Review**: Check signal patterns
3. **Position Review**: Verify portfolio alignment
4. **Performance Review**: Compare with backtest

---

## 🎯 Best Practices

### **Before Each Trading Day**:
1. ✅ Ensure TWS is running
2. ✅ Activate Python environment
3. ✅ Check account status
4. ✅ Review previous day's results

### **After Each Trading Day**:
1. ✅ Verify trades executed correctly
2. ✅ Check positions in TWS
3. ✅ Review execution logs
4. ✅ Monitor P&L

### **Weekly Maintenance**:
1. ✅ Run transaction cost analysis
2. ✅ Clean up old logs (optional)
3. ✅ Review system performance
4. ✅ Update training if needed

---

## 🚀 Next Steps

### **When Ready for Automation**:
1. **Windows Task Scheduler**: Most reliable for production
2. **Enhanced Python Scheduler**: For testing automation
3. **Cloud Deployment**: For 24/7 operation

### **Advanced Features**:
1. **Risk Management**: Add position limits
2. **Performance Monitoring**: Real-time P&L tracking
3. **Alert System**: Email/SMS notifications
4. **Backup Systems**: Redundant execution

---

## 📞 Support

### **If Something Goes Wrong**:
1. **Check logs**: Look for error messages
2. **Verify connections**: TWS and IBKR
3. **Review data**: Signal and execution files
4. **Clean restart**: Use cleanup script and restart

### **Emergency Procedures**:
1. **Stop all trading**: Close TWS
2. **Close positions**: Manual close in TWS
3. **Review system**: Check logs and files
4. **Restart clean**: Use cleanup and restart

---

*Last Updated: July 30, 2025*
*System Version: Live Trading v1.0* 
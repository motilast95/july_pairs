# Live Trading System Guide

## Overview

This guide explains how to use the automated pairs trading system that connects to your IBKR paper trading account.

## System Components

### 1. Phase 1: Training (One-time setup)
- **File**: `src/trading/live_trading_setup.py`
- **Purpose**: Select pairs and calculate hedge ratios
- **Frequency**: Every 6 months
- **Command**: `python -m src.trading.live_trading_setup`

### 2. Phase 2: Daily Signal Generation
- **File**: `src/trading/daily_signal_generator.py`
- **Purpose**: Generate trading signals at 5:00 PM
- **Frequency**: Daily
- **Command**: `python -m src.trading.daily_signal_generator`

### 3. Phase 3: Daily Trade Execution
- **File**: `src/trading/daily_executor.py`
- **Purpose**: Execute trades at 9:30 AM
- **Frequency**: Daily
- **Command**: `python -m src.trading.daily_executor`

### 4. Scheduler (Optional)
- **File**: `src/trading/scheduler.py`
- **Purpose**: Automate daily processes
- **Command**: `python -m src.trading.scheduler`

## Setup Instructions

### Prerequisites
1. **IBKR TWS/Gateway** running and connected
2. **Paper trading account** active
3. **Python virtual environment** activated
4. **Dependencies installed**: `pip install -r requirements.txt`

### Initial Setup (One-time)
```bash
# 1. Run Phase 1 training
python -m src.trading.live_trading_setup

# 2. Verify training results
ls results/live_trading/
```

### Daily Operation

#### Option 1: Manual (Recommended for learning)
```bash
# 5:00 PM - Generate signals
python -m src.trading.daily_signal_generator

# 9:30 AM next day - Execute trades
python -m src.trading.daily_executor
```

#### Option 2: Automated
```bash
# Start the scheduler (runs continuously)
python -m src.trading.scheduler
```

## File Structure

```
results/live_trading/
├── training_summary_*.json    # Phase 1 results
├── signals/
│   └── signals_YYYYMMDD.json  # Daily signals
├── executions/
│   └── execution_YYYYMMDD.json # Daily results
└── logs/                      # System logs
```

## Monitoring

### Check Signal Generation
```bash
# View latest signals
cat results/live_trading/signals/signals_$(date +%Y%m%d).json
```

### Check Trade Execution
```bash
# View latest execution results
cat results/live_trading/executions/execution_$(date +%Y%m%d).json
```

### Check IBKR Positions
- Open TWS/Gateway
- View Account → Positions
- Verify trades were executed correctly

## Troubleshooting

### Common Issues

1. **"No training summary files found"**
   - Run Phase 1 first: `python -m src.trading.live_trading_setup`

2. **"Connection failed"**
   - Ensure TWS/Gateway is running
   - Check paper trading port (7497)
   - Verify API connections enabled

3. **"No signal file found"**
   - Run signal generation first: `python -m src.trading.daily_signal_generator`

4. **"Orders not filled"**
   - Check market hours (9:30 AM - 4:00 PM ET)
   - Verify sufficient account balance
   - Check for trading restrictions

### Logs
- Check `results/live_trading/logs/` for detailed logs
- Monitor console output for real-time status

## Safety Features

### Paper Trading Only
- All trades go to paper account
- No real money at risk
- Perfect for learning and testing

### Position Limits
- Default: 100 shares per position
- Adjustable in `daily_executor.py`
- Risk management built-in

### Error Handling
- Automatic reconnection to IBKR
- Graceful failure handling
- Detailed error logging

## Performance Monitoring

### Key Metrics
- **Sharpe Ratio**: Target > 1.0
- **Win Rate**: Percentage of profitable trades
- **Drawdown**: Maximum loss from peak
- **Transaction Costs**: Commission impact

### Expected Results
Based on backtesting:
- **Sharpe Ratio**: 1.170
- **Strategy**: Mean-reverting pairs
- **Frequency**: Daily signals
- **Holding Period**: Variable (based on exit signals)

## Maintenance

### Weekly
- Review execution logs
- Check IBKR account status
- Verify signal quality

### Monthly
- Analyze performance metrics
- Review pair selection
- Update training data if needed

### Quarterly
- Re-run Phase 1 training
- Update hedge ratios
- Optimize parameters

## Support

### Getting Help
1. Check logs in `results/live_trading/logs/`
2. Review this guide
3. Test individual components
4. Verify IBKR connection

### Emergency Stop
- Stop scheduler: `Ctrl+C`
- Close TWS/Gateway
- Check positions in IBKR

## Next Steps

1. **Start with manual operation** to learn the system
2. **Monitor performance** for first few weeks
3. **Graduate to automated scheduler** when comfortable
4. **Consider parameter optimization** based on results
5. **Scale up position sizes** gradually

---

**Remember**: This is a learning system. Start small, monitor closely, and understand each component before scaling up. 
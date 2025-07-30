"""
IBKR Configuration Template
Copy this file to ibkr_config.py and fill in your actual values
"""

# IBKR Connection Settings
IBKR_HOST = "127.0.0.1"  # Local host for TWS/IB Gateway
IBKR_PORT = 7497  # Paper trading port (7496 for live)
IBKR_CLIENT_ID = 1  # Unique client ID

# Account Settings
ACCOUNT_ID = "YOUR_ACCOUNT_ID"  # Your IBKR account number

# Trading Settings
PAPER_TRADING = True  # Set to False for live trading
MAX_POSITION_SIZE = 1000  # Maximum dollars per position
MAX_DAILY_TRADES = 10  # Maximum trades per day

# Risk Management
STOP_LOSS_PCT = 0.05  # 5% stop loss
TAKE_PROFIT_PCT = 0.10  # 10% take profit
MAX_PORTFOLIO_RISK = 0.02  # 2% max portfolio risk per trade

# Data Settings
DATA_SOURCE = "yahoo"  # "yahoo" or "ibkr"
UPDATE_FREQUENCY = "daily"  # "daily" or "intraday"

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "logs/live_trading.log" 
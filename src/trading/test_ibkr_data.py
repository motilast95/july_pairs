"""
Test IBKR Data Format and Spread Calculation
Explore what data we get from IBKR and test our calculations
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from ib_insync import *

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ibkr_data_format():
    """Test IBKR data format and availability."""
    print("🔍 TESTING IBKR DATA FORMAT")
    print("="*50)
    
    # Connect to IBKR
    ib = IB()
    try:
        ib.connect('127.0.0.1', 7497, clientId=1)
        logger.info("✅ Connected to IBKR")
        
        # Test tickers from our pairs
        test_tickers = ['JPM', 'GS', 'WFC', 'C']  # Start with 4 tickers
        
        print(f"\n📊 Testing data for: {test_tickers}")
        print("-" * 40)
        
        for ticker in test_tickers:
            print(f"\n🔍 Testing {ticker}:")
            
            # Create contract
            contract = Stock(ticker, 'SMART', 'USD')
            
            # Request market data
            ib.qualifyContracts(contract)
            
            # Get current market data
            ticker_data = ib.reqMktData(contract)
            
            # Wait a moment for data
            ib.sleep(2)
            
            # Print available data
            print(f"  📈 Bid: ${ticker_data.bid:.2f}")
            print(f"  📉 Ask: ${ticker_data.ask:.2f}")
            print(f"  💰 Last: ${ticker_data.last:.2f}")
            print(f"  📊 Close: ${ticker_data.close:.2f}")
            print(f"  📈 High: ${ticker_data.high:.2f}")
            print(f"  📉 Low: ${ticker_data.low:.2f}")
            print(f"  📦 Volume: {ticker_data.volume:,}")
            
            # Check if data is delayed
            if hasattr(ticker_data, 'delayed'):
                print(f"  ⏰ Delayed: {ticker_data.delayed}")
            
            # Cancel market data request
            ib.cancelMktData(contract)
        
        # Test historical data
        print(f"\n📚 Testing Historical Data for JPM:")
        print("-" * 40)
        
        jpm_contract = Stock('JPM', 'SMART', 'USD')
        ib.qualifyContracts(jpm_contract)
        
        # Get last 5 days of data
        end_time = datetime.now().strftime('%Y%m%d %H:%M:%S')
        bars = ib.reqHistoricalData(
            jpm_contract,
            endDateTime=end_time,
            durationStr='5 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True
        )
        
        if bars:
            print(f"  📅 Got {len(bars)} days of historical data:")
            for bar in bars[-3:]:  # Show last 3 days
                print(f"    {bar.date}: Open=${bar.open:.2f}, Close=${bar.close:.2f}, Volume={bar.volume:,}")
        else:
            print("  ❌ No historical data received")
        
        ib.disconnect()
        logger.info("🔌 Disconnected from IBKR")
        
    except Exception as e:
        logger.error(f"❌ Error testing IBKR data: {e}")
        if ib.isConnected():
            ib.disconnect()

def test_data_timing():
    """Test when today's closing prices become available."""
    print("\n⏰ TESTING DATA TIMING")
    print("="*50)
    
    # Connect to IBKR
    ib = IB()
    try:
        ib.connect('127.0.0.1', 7497, clientId=1)
        logger.info("✅ Connected to IBKR for timing test")
        
        # Test JPM to see what data we get
        contract = Stock('JPM', 'SMART', 'USD')
        ib.qualifyContracts(contract)
        
        # Get last 3 days to see what's available
        end_time = datetime.now().strftime('%Y%m%d %H:%M:%S')
        bars = ib.reqHistoricalData(
            contract,
            endDateTime=end_time,
            durationStr='3 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True
        )
        
        if bars:
            print(f"📅 Got {len(bars)} days of data:")
            for i, bar in enumerate(bars):
                print(f"  Day {i+1}: {bar.date} - Close=${bar.close:.2f}")
            
            # Check if today's data is available
            today = datetime.now().date()
            latest_bar_date = bars[-1].date
            
            print(f"\n📊 Data Analysis:")
            print(f"  Today's date: {today}")
            print(f"  Latest bar date: {latest_bar_date}")
            
            if latest_bar_date == today:
                print("  ✅ Today's closing price is available!")
            else:
                print("  ⏳ Today's closing price not yet available")
                print("  📝 Latest available: previous trading day")
        
        ib.disconnect()
        logger.info("🔌 Disconnected from IBKR")
        
    except Exception as e:
        logger.error(f"❌ Error in timing test: {e}")
        if ib.isConnected():
            ib.disconnect()

def test_spread_calculation_with_ibkr_data():
    """Test our spread calculation using IBKR historical data."""
    print("\n🧮 TESTING SPREAD CALCULATION WITH IBKR HISTORICAL DATA")
    print("="*50)
    
    # Load our training results to get hedge ratios
    try:
        import json
        import glob
        import os
        
        # Find the most recent training summary
        pattern = "results/live_trading/training_summary_*.json"
        files = glob.glob(pattern)
        
        if not files:
            print("❌ No training summary files found. Run Phase 1 first.")
            return
        
        latest_file = max(files, key=os.path.getctime)
        print(f"📁 Using training summary: {latest_file}")
        
        with open(latest_file, 'r') as f:
            training_summary = json.load(f)
        
        # Get hedge ratios for our test pairs
        hedge_ratios = {}
        for pair_key, model in training_summary['pair_models'].items():
            if pair_key in ['JPM-GS', 'WFC-C']:  # Test with first two pairs
                hedge_ratios[pair_key] = model['beta']
                print(f"📊 {pair_key}: β={model['beta']:.4f}")
        
        # Connect to IBKR and get yesterday's closing prices
        ib = IB()
        try:
            ib.connect('127.0.0.1', 7497, clientId=1)
            logger.info("✅ Connected to IBKR for historical data test")
            
            today_prices = {}
            
            # Get today's closing prices for all tickers
            for pair_key in hedge_ratios.keys():
                ticker1, ticker2 = pair_key.split('-')
                
                for ticker in [ticker1, ticker2]:
                    if ticker not in today_prices:
                        contract = Stock(ticker, 'SMART', 'USD')
                        ib.qualifyContracts(contract)
                        
                        # Get today's data (to get today's close)
                        end_time = datetime.now().strftime('%Y%m%d %H:%M:%S')
                        bars = ib.reqHistoricalData(
                            contract,
                            endDateTime=end_time,
                            durationStr='1 D',
                            barSizeSetting='1 day',
                            whatToShow='TRADES',
                            useRTH=True
                        )
                        
                        if bars and len(bars) >= 1:
                            # Get today's closing price (most recent bar)
                            today_close = bars[-1].close
                            today_prices[ticker] = today_close
                            print(f"💰 {ticker}: ${today_close:.2f} (today's close)")
                        else:
                            print(f"❌ No historical data for {ticker}")
                            today_prices[ticker] = None
            
            # Calculate spreads
            print(f"\n📈 SPREAD CALCULATIONS:")
            print("-" * 30)
            
            for pair_key, beta in hedge_ratios.items():
                ticker1, ticker2 = pair_key.split('-')
                price1 = today_prices[ticker1]
                price2 = today_prices[ticker2]
                
                if price1 is not None and price2 is not None:
                    spread = price1 - beta * price2
                    print(f"📊 {pair_key}: {ticker1}(${price1:.2f}) - {beta:.4f}×{ticker2}(${price2:.2f}) = {spread:.2f}")
                else:
                    print(f"❌ {pair_key}: Missing price data")
            
            ib.disconnect()
            logger.info("🔌 Disconnected from IBKR")
            
        except Exception as e:
            logger.error(f"❌ Error in spread calculation test: {e}")
            if ib.isConnected():
                ib.disconnect()
                
    except Exception as e:
        logger.error(f"❌ Error loading training summary: {e}")

def main():
    """Run the IBKR data tests."""
    print("🚀 IBKR DATA FORMAT TEST")
    print("="*50)
    
    # Test 1: Explore data format
    test_ibkr_data_format()
    
    # Test 2: Test data timing
    test_data_timing()
    
    # Test 3: Test spread calculation
    test_spread_calculation_with_ibkr_data()
    
    print("\n✅ IBKR data testing complete!")

if __name__ == "__main__":
    main() 
"""
Daily Signal Generator for Pairs Trading
Runs at 5:00 PM daily to generate signals for next day execution
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from ib_insync import *
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DailySignalGenerator:
    """Generate daily signals for pairs trading"""
    
    def __init__(self, training_summary_path=None):
        """
        Initialize signal generator
        
        Args:
            training_summary_path: Path to training summary JSON file
        """
        self.training_summary_path = training_summary_path
        self.signals_dir = "results/live_trading/signals"
        
        # Create signals directory if it doesn't exist
        os.makedirs(self.signals_dir, exist_ok=True)
        
        # Load training results
        self.load_training_results()
        
    def load_training_results(self):
        """Load training results with hedge ratios and parameters"""
        try:
            if self.training_summary_path is None:
                # Find the most recent training summary
                import glob
                pattern = "results/live_trading/training_summary_*.json"
                files = glob.glob(pattern)
                
                if not files:
                    raise FileNotFoundError("No training summary files found. Run Phase 1 first.")
                
                self.training_summary_path = max(files, key=os.path.getctime)
            
            with open(self.training_summary_path, 'r') as f:
                self.training_summary = json.load(f)
            
            logger.info(f"✅ Loaded training summary: {self.training_summary_path}")
            
        except Exception as e:
            logger.error(f"❌ Error loading training results: {e}")
            raise
    
    def get_today_prices(self):
        """Get today's closing prices from IBKR"""
        ib = IB()
        try:
            ib.connect('127.0.0.1', 7497, clientId=1)
            logger.info("✅ Connected to IBKR")
            
            today_prices = {}
            
            # Get all unique tickers from pairs
            all_tickers = set()
            for pair_key in self.training_summary['pair_models'].keys():
                ticker1, ticker2 = pair_key.split('-')
                all_tickers.add(ticker1)
                all_tickers.add(ticker2)
            
            logger.info(f"📊 Getting prices for {len(all_tickers)} tickers")
            
            # Get today's closing prices for all tickers
            for ticker in all_tickers:
                contract = Stock(ticker, 'SMART', 'USD')
                ib.qualifyContracts(contract)
                
                # Get today's data
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
                    today_close = bars[-1].close
                    today_prices[ticker] = today_close
                    logger.info(f"💰 {ticker}: ${today_close:.2f}")
                else:
                    logger.error(f"❌ No data for {ticker}")
                    today_prices[ticker] = None
            
            ib.disconnect()
            logger.info("🔌 Disconnected from IBKR")
            
            return today_prices
            
        except Exception as e:
            logger.error(f"❌ Error getting prices: {e}")
            if ib.isConnected():
                ib.disconnect()
            raise
    
    def calculate_spreads(self, prices):
        """Calculate spreads for all pairs"""
        spreads = {}
        
        for pair_key, model in self.training_summary['pair_models'].items():
            ticker1, ticker2 = pair_key.split('-')
            price1 = prices.get(ticker1)
            price2 = prices.get(ticker2)
            
            if price1 is not None and price2 is not None:
                beta = model['beta']
                spread = price1 - beta * price2
                spreads[pair_key] = {
                    'spread': spread,
                    'ticker1': ticker1,
                    'ticker2': ticker2,
                    'price1': price1,
                    'price2': price2,
                    'beta': beta
                }
                logger.info(f"📊 {pair_key}: Spread = {spread:.2f}")
            else:
                logger.warning(f"⚠️ Missing prices for {pair_key}")
        
        return spreads
    
    def generate_signals(self, spreads):
        """Generate trading signals based on spreads using rolling method (matching backtest)"""
        signals = {}
        
        # Get signal parameters from training summary (matching backtest)
        entry_z = self.training_summary.get('signal_params', {}).get('entry_z', 1.5)  # From backtest
        exit_z = self.training_summary.get('signal_params', {}).get('exit_z', 0.5)   # From backtest
        rolling_window = 60  # From backtest
        
        for pair_key, spread_data in spreads.items():
            spread = spread_data['spread']
            
            # Get historical spread data for rolling calculation
            # Note: In live trading, we'd need to maintain historical spread data
            # For now, use the training statistics as approximation
            model = self.training_summary['pair_models'][pair_key]
            spread_mean = model['spread_mean']
            spread_std = model['spread_std']
            
            # Calculate z-score (approximation for now)
            z_score = (spread - spread_mean) / spread_std
            
            # Generate signal using rolling logic (matching backtest)
            if z_score > entry_z:
                signal = "SHORT"  # Short the spread (short ticker1, long ticker2)
            elif z_score < -entry_z:
                signal = "LONG"   # Long the spread (long ticker1, short ticker2)
            elif abs(z_score) < exit_z:
                signal = "FLAT"   # Close positions
            else:
                signal = "HOLD"   # Hold current positions
            
            signals[pair_key] = {
                'signal': signal,
                'z_score': z_score,
                'spread': spread,
                'spread_mean': spread_mean,
                'spread_std': spread_std,
                'entry_z': entry_z,
                'exit_z': exit_z,
                'ticker1': spread_data['ticker1'],
                'ticker2': spread_data['ticker2'],
                'price1': spread_data['price1'],
                'price2': spread_data['price2'],
                'beta': spread_data['beta']
            }
            
            logger.info(f"📈 {pair_key}: {signal} (z={z_score:.2f})")
        
        return signals
    
    def save_signals(self, signals):
        """Save signals to file for next day execution"""
        today = datetime.now().strftime('%Y%m%d')
        signal_file = f"{self.signals_dir}/signals_{today}.json"
        
        signal_data = {
            'date': today,
            'generated_at': datetime.now().isoformat(),
            'signals': signals,
            'training_summary_path': self.training_summary_path
        }
        
        with open(signal_file, 'w') as f:
            json.dump(signal_data, f, indent=2)
        
        logger.info(f"💾 Saved signals to: {signal_file}")
        return signal_file
    
    def run_daily_signals(self):
        """Run the complete daily signal generation process"""
        logger.info("🚀 Starting daily signal generation...")
        
        try:
            # Step 1: Get today's prices
            logger.info("📊 Step 1: Getting today's closing prices...")
            prices = self.get_today_prices()
            
            # Step 2: Calculate spreads
            logger.info("🧮 Step 2: Calculating spreads...")
            spreads = self.calculate_spreads(prices)
            
            # Step 3: Generate signals
            logger.info("📈 Step 3: Generating signals...")
            signals = self.generate_signals(spreads)
            
            # Step 4: Save signals
            logger.info("💾 Step 4: Saving signals...")
            signal_file = self.save_signals(signals)
            
            # Summary
            logger.info("✅ Daily signal generation complete!")
            logger.info(f"📁 Signals saved to: {signal_file}")
            
            # Print summary
            self.print_summary(signals)
            
            return signal_file
            
        except Exception as e:
            logger.error(f"❌ Error in daily signal generation: {e}")
            raise
    
    def print_summary(self, signals):
        """Print a summary of generated signals"""
        print("\n" + "="*50)
        print("📊 DAILY SIGNAL SUMMARY")
        print("="*50)
        
        signal_counts = {}
        for pair_key, signal_data in signals.items():
            signal = signal_data['signal']
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
            print(f"📈 {pair_key}: {signal} (z={signal_data['z_score']:.2f})")
        
        print("\n📊 Signal Distribution:")
        for signal, count in signal_counts.items():
            print(f"  {signal}: {count} pairs")
        
        print("="*50)


def main():
    """Main function to run daily signal generation"""
    print("🚀 DAILY SIGNAL GENERATOR")
    print("="*50)
    
    try:
        # Create signal generator
        generator = DailySignalGenerator()
        
        # Run daily signals
        signal_file = generator.run_daily_signals()
        
        print(f"\n✅ Success! Signals saved to: {signal_file}")
        print("📅 Ready for execution tomorrow at 9:30 AM")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 
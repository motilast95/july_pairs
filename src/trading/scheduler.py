"""
Simple Scheduler for Daily Pairs Trading
Runs signal generation at 5:00 PM and execution at 9:30 AM
"""

import schedule
import time
import logging
from datetime import datetime
import subprocess
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingScheduler:
    """Simple scheduler for daily trading operations"""
    
    def __init__(self):
        self.log_dir = "results/live_trading/logs"
        os.makedirs(self.log_dir, exist_ok=True)
    
    def run_signal_generation(self):
        """Run daily signal generation at 5:00 PM"""
        logger.info("🚀 Starting scheduled signal generation...")
        
        try:
            # Run the signal generator
            result = subprocess.run([
                sys.executable, "-m", "src.trading.daily_signal_generator"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Signal generation completed successfully")
                logger.info(f"📝 Output: {result.stdout}")
            else:
                logger.error(f"❌ Signal generation failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Error running signal generation: {e}")
    
    def run_trade_execution(self):
        """Run daily trade execution at 9:30 AM"""
        logger.info("🚀 Starting scheduled trade execution...")
        
        try:
            # Run the trade executor
            result = subprocess.run([
                sys.executable, "-m", "src.trading.daily_executor"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Trade execution completed successfully")
                logger.info(f"📝 Output: {result.stdout}")
            else:
                logger.error(f"❌ Trade execution failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Error running trade execution: {e}")
    
    def setup_schedule(self):
        """Set up the daily schedule"""
        logger.info("📅 Setting up daily trading schedule...")
        
        # Schedule signal generation at 5:00 PM
        schedule.every().day.at("17:00").do(self.run_signal_generation)
        logger.info("⏰ Scheduled signal generation at 5:00 PM")
        
        # Schedule trade execution at 9:30 AM
        schedule.every().day.at("09:30").do(self.run_trade_execution)
        logger.info("⏰ Scheduled trade execution at 9:30 AM")
        
        logger.info("✅ Schedule setup complete!")
    
    def run_scheduler(self):
        """Run the scheduler continuously"""
        logger.info("🔄 Starting trading scheduler...")
        logger.info("📅 Monitoring for scheduled tasks...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main function to run the scheduler"""
    print("🚀 TRADING SCHEDULER")
    print("="*50)
    
    scheduler = TradingScheduler()
    scheduler.setup_schedule()
    
    print("\n📅 Daily Schedule:")
    print("  5:00 PM - Signal Generation")
    print("  9:30 AM - Trade Execution")
    print("\n🔄 Scheduler is running... (Press Ctrl+C to stop)")
    
    try:
        scheduler.run_scheduler()
    except KeyboardInterrupt:
        print("\n⏹️ Scheduler stopped by user")
        return 0


if __name__ == "__main__":
    exit(main()) 
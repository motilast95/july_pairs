"""
Robust Trading Scheduler with Enhanced Error Handling
Better suited for long-term background operation
"""

import schedule
import time
import logging
from datetime import datetime
import subprocess
import sys
import os
import json
import threading
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('results/live_trading/logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RobustTradingScheduler:
    """Enhanced scheduler with better error handling and monitoring"""
    
    def __init__(self):
        self.log_dir = "results/live_trading/logs"
        self.status_file = "results/live_trading/scheduler_status.json"
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Track execution status
        self.last_signal_run = None
        self.last_execution_run = None
        self.error_count = 0
        self.max_errors = 5
        
    def update_status(self, task_type, success, error=None):
        """Update scheduler status file"""
        status = {
            'last_update': datetime.now().isoformat(),
            'last_signal_run': self.last_signal_run,
            'last_execution_run': self.last_execution_run,
            'error_count': self.error_count,
            'last_error': error
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def run_signal_generation(self):
        """Run daily signal generation with enhanced error handling"""
        logger.info("🚀 Starting scheduled signal generation...")
        
        try:
            # Run the signal generator
            result = subprocess.run([
                sys.executable, "-m", "src.trading.daily_signal_generator"
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            if result.returncode == 0:
                logger.info("✅ Signal generation completed successfully")
                self.last_signal_run = datetime.now().isoformat()
                self.error_count = 0  # Reset error count on success
                self.update_status('signal', True)
            else:
                logger.error(f"❌ Signal generation failed: {result.stderr}")
                self.error_count += 1
                self.update_status('signal', False, result.stderr)
                
        except subprocess.TimeoutExpired:
            error_msg = "Signal generation timed out after 5 minutes"
            logger.error(f"❌ {error_msg}")
            self.error_count += 1
            self.update_status('signal', False, error_msg)
        except Exception as e:
            logger.error(f"❌ Error running signal generation: {e}")
            self.error_count += 1
            self.update_status('signal', False, str(e))
    
    def run_trade_execution(self):
        """Run daily trade execution with enhanced error handling"""
        logger.info("🚀 Starting scheduled trade execution...")
        
        try:
            # Run the trade executor
            result = subprocess.run([
                sys.executable, "-m", "src.trading.daily_executor"
            ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                logger.info("✅ Trade execution completed successfully")
                self.last_execution_run = datetime.now().isoformat()
                self.error_count = 0  # Reset error count on success
                self.update_status('execution', True)
            else:
                logger.error(f"❌ Trade execution failed: {result.stderr}")
                self.error_count += 1
                self.update_status('execution', False, result.stderr)
                
        except subprocess.TimeoutExpired:
            error_msg = "Trade execution timed out after 10 minutes"
            logger.error(f"❌ {error_msg}")
            self.error_count += 1
            self.update_status('execution', False, error_msg)
        except Exception as e:
            logger.error(f"❌ Error running trade execution: {e}")
            self.error_count += 1
            self.update_status('execution', False, str(e))
    
    def check_health(self):
        """Check system health and log status"""
        logger.info(f"📊 Scheduler Health Check:")
        logger.info(f"  - Error count: {self.error_count}/{self.max_errors}")
        logger.info(f"  - Last signal run: {self.last_signal_run}")
        logger.info(f"  - Last execution run: {self.last_execution_run}")
        
        # Alert if too many errors
        if self.error_count >= self.max_errors:
            logger.error(f"⚠️ WARNING: {self.error_count} consecutive errors!")
            logger.error("Consider restarting the scheduler or checking system status")
    
    def setup_schedule(self):
        """Set up the daily schedule"""
        logger.info("📅 Setting up daily trading schedule...")
        
        # Schedule signal generation at 5:00 PM
        schedule.every().day.at("17:00").do(self.run_signal_generation)
        logger.info("⏰ Scheduled signal generation at 5:00 PM")
        
        # Schedule trade execution at 9:30 AM
        schedule.every().day.at("09:30").do(self.run_trade_execution)
        logger.info("⏰ Scheduled trade execution at 9:30 AM")
        
        # Health check every hour
        schedule.every().hour.do(self.check_health)
        logger.info("⏰ Scheduled health check every hour")
        
        logger.info("✅ Schedule setup complete!")
    
    def run_scheduler(self):
        """Run the scheduler with enhanced monitoring"""
        logger.info("🔄 Starting robust trading scheduler...")
        logger.info("📅 Monitoring for scheduled tasks...")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
                # Auto-restart if too many errors
                if self.error_count >= self.max_errors:
                    logger.error("🔄 Too many errors, restarting scheduler...")
                    self.error_count = 0
                    time.sleep(300)  # Wait 5 minutes before continuing
                    
            except KeyboardInterrupt:
                logger.info("⏹️ Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected scheduler error: {e}")
                time.sleep(60)  # Wait before retrying


def main():
    """Main function to run the robust scheduler"""
    print("🚀 ROBUST TRADING SCHEDULER")
    print("="*50)
    
    scheduler = RobustTradingScheduler()
    scheduler.setup_schedule()
    
    print("\n📅 Daily Schedule:")
    print("  5:00 PM - Signal Generation")
    print("  9:30 AM - Trade Execution")
    print("  Every Hour - Health Check")
    print("\n🔄 Scheduler is running... (Press Ctrl+C to stop)")
    print("📊 Status file: results/live_trading/scheduler_status.json")
    print("📝 Log file: results/live_trading/logs/scheduler.log")
    
    try:
        scheduler.run_scheduler()
    except KeyboardInterrupt:
        print("\n⏹️ Scheduler stopped by user")
        return 0


if __name__ == "__main__":
    exit(main()) 
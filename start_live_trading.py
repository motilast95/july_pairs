#!/usr/bin/env python3
"""
Quick Start Script for Live Trading System
Provides easy options to run different components
"""

import sys
import os
import subprocess
from datetime import datetime

def print_banner():
    """Print the system banner"""
    print("=" * 60)
    print("🚀 PAIRS TRADING LIVE SYSTEM")
    print("=" * 60)
    print("📊 IBKR Paper Trading Integration")
    print("📈 Mean-Reverting Pairs Strategy")
    print("⏰ Automated Daily Execution")
    print("=" * 60)

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    print(f"📝 Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with error: {e}")
        return False

def main():
    """Main function with menu options"""
    print_banner()
    
    while True:
        print("\n📋 Available Options:")
        print("1. 🔧 Phase 1: Initial Training (One-time setup)")
        print("2. 📊 Generate Signals (5:00 PM daily)")
        print("3. 📈 Execute Trades (9:30 AM daily)")
        print("4. 🔄 Start Automated Scheduler")
        print("5. 📖 View Latest Signals")
        print("6. 📊 View Latest Execution Results")
        print("7. 💸 Analyze Transaction Costs")
        print("8. 🧪 Test IBKR Connection")
        print("9. ❌ Exit")
        
        choice = input("\n🎯 Select an option (1-9): ").strip()
        
        if choice == "1":
            # Phase 1: Training
            success = run_command(
                "python -m src.trading.live_trading_setup",
                "Phase 1 Training"
            )
            if success:
                print("✅ Training completed! You can now run daily operations.")
        
        elif choice == "2":
            # Generate Signals
            run_command(
                "python -m src.trading.daily_signal_generator",
                "Signal Generation"
            )
        
        elif choice == "3":
            # Execute Trades
            run_command(
                "python -m src.trading.daily_executor",
                "Trade Execution"
            )
        
        elif choice == "4":
            # Start Scheduler
            print("\n🔄 Starting automated scheduler...")
            print("📅 Will run signal generation at 5:00 PM")
            print("📅 Will run trade execution at 9:30 AM")
            print("⏹️ Press Ctrl+C to stop the scheduler")
            
            try:
                subprocess.run(["python", "-m", "src.trading.scheduler"])
            except KeyboardInterrupt:
                print("\n⏹️ Scheduler stopped by user")
        
        elif choice == "5":
            # View Latest Signals
            today = datetime.now().strftime('%Y%m%d')
            signal_file = f"results/live_trading/signals/signals_{today}.json"
            
            if os.path.exists(signal_file):
                print(f"\n📊 Latest Signals ({today}):")
                with open(signal_file, 'r') as f:
                    import json
                    data = json.load(f)
                    for pair, signal in data['signals'].items():
                        print(f"  📈 {pair}: {signal['signal']} (z={signal['z_score']:.2f})")
            else:
                print(f"❌ No signal file found for today ({today})")
                print("💡 Run signal generation first (option 2)")
        
        elif choice == "6":
            # View Latest Execution Results
            today = datetime.now().strftime('%Y%m%d')
            execution_file = f"results/live_trading/executions/execution_{today}.json"
            
            if os.path.exists(execution_file):
                print(f"\n📊 Latest Execution Results ({today}):")
                with open(execution_file, 'r') as f:
                    import json
                    data = json.load(f)
                    print(f"  📈 Total trades: {data['total_trades']}")
                    for trade in data['executed_trades']:
                        print(f"  📈 {trade['action']} {trade['quantity']} {trade['ticker']} @ ${trade['fill_price']:.2f}")
            else:
                print(f"❌ No execution file found for today ({today})")
                print("💡 Run trade execution first (option 3)")
        
        elif choice == "7":
            # Analyze Transaction Costs
            run_command(
                "python -m src.trading.transaction_cost_analyzer",
                "Transaction Cost Analysis"
            )
        
        elif choice == "8":
            # Test IBKR Connection
            run_command(
                "python -m src.trading.ibkr_connection",
                "IBKR Connection Test"
            )
        
        elif choice == "9":
            print("\n👋 Goodbye! Happy trading!")
            break
        
        else:
            print("❌ Invalid option. Please select 1-8.")
        
        input("\n⏸️ Press Enter to continue...")

if __name__ == "__main__":
    main() 
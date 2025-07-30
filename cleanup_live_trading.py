"""
Cleanup script for live trading data
Deletes all logs, signals, executions, and analysis files
"""

import os
import glob
import shutil

def cleanup_live_trading():
    """Clean up all live trading data"""
    print("🧹 CLEANING UP LIVE TRADING DATA")
    print("="*50)
    
    # Files to delete
    patterns = [
        "results/live_trading/executions/*.json",
        "results/live_trading/signals/*.json", 
        "results/live_trading/training_summary_*.json",
        "results/live_trading/valid_pairs_*.txt",
        "results/transaction_cost_analysis.png"
    ]
    
    deleted_count = 0
    
    for pattern in patterns:
        files = glob.glob(pattern)
        for file in files:
            try:
                os.remove(file)
                print(f"🗑️  Deleted: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️  Could not delete {file}: {e}")
    
    print(f"\n✅ Cleanup complete! Deleted {deleted_count} files")
    print("📝 Note: You still need to manually close positions in TWS")
    print("🎯 Ready for fresh testing!")

if __name__ == "__main__":
    cleanup_live_trading() 
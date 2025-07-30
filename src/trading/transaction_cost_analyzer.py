"""
Transaction Cost Analyzer for Live Trading
Analyzes actual transaction costs from IBKR executions
"""

import json
import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import matplotlib.pyplot as plt

class TransactionCostAnalyzer:
    """Analyze transaction costs from live trading data"""
    
    def __init__(self):
        self.executions_dir = "results/live_trading/executions"
        self.signals_dir = "results/live_trading/signals"
        
    def load_execution_data(self):
        """Load all execution data"""
        execution_files = glob.glob(f"{self.executions_dir}/execution_*.json")
        
        all_trades = []
        daily_summary = []
        
        for file_path in execution_files:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Add daily summary
            daily_summary.append({
                'date': data['date'],
                'total_trades': data['total_trades'],
                'total_commission': data.get('total_commission', 0),
                'total_trade_value': data.get('total_trade_value', 0),
                'commission_bps': data.get('commission_bps', 0)
            })
            
            # Add individual trades
            for trade in data['executed_trades']:
                trade['date'] = data['date']
                all_trades.append(trade)
        
        return pd.DataFrame(all_trades), pd.DataFrame(daily_summary)
    
    def analyze_costs(self):
        """Analyze transaction costs"""
        trades_df, daily_df = self.load_execution_data()
        
        if trades_df.empty:
            print("❌ No execution data found")
            return
        
        print("📊 TRANSACTION COST ANALYSIS")
        print("="*50)
        
        # Overall statistics
        total_commission = trades_df['commission'].sum()
        total_value = (trades_df['quantity'] * trades_df['fill_price']).abs().sum()
        avg_commission_bps = (total_commission / total_value * 10000) if total_value > 0 else 0
        
        print(f"💰 Total Trade Value: ${total_value:,.2f}")
        print(f"💸 Total Commission: ${total_commission:.2f}")
        print(f"📊 Average Commission Rate: {avg_commission_bps:.1f} bps")
        print(f"📈 Total Trades: {len(trades_df)}")
        print(f"📅 Trading Days: {len(daily_df)}")
        
        # Daily breakdown
        print(f"\n📅 DAILY BREAKDOWN:")
        print("-" * 30)
        for _, day in daily_df.iterrows():
            print(f"{day['date']}: {day['total_trades']} trades, ${day['total_commission']:.2f} commission ({day['commission_bps']:.1f} bps)")
        
        # Commission by ticker
        print(f"\n📊 COMMISSION BY TICKER:")
        print("-" * 30)
        ticker_comm = trades_df.groupby('ticker')['commission'].agg(['sum', 'count']).sort_values('sum', ascending=False)
        for ticker, row in ticker_comm.iterrows():
            print(f"{ticker}: ${row['sum']:.2f} ({row['count']} trades)")
        
        # Commission by pair
        print(f"\n📊 COMMISSION BY PAIR:")
        print("-" * 30)
        pair_comm = trades_df.groupby('pair')['commission'].agg(['sum', 'count']).sort_values('sum', ascending=False)
        for pair, row in pair_comm.iterrows():
            print(f"{pair}: ${row['sum']:.2f} ({row['count']} trades)")
        
        return trades_df, daily_df
    
    def plot_costs(self, trades_df, daily_df):
        """Create visualizations of transaction costs"""
        if trades_df.empty:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Transaction Cost Analysis', fontsize=16)
        
        # Daily commission
        daily_df['date'] = pd.to_datetime(daily_df['date'], format='%Y%m%d')
        axes[0, 0].bar(daily_df['date'], daily_df['total_commission'])
        axes[0, 0].set_title('Daily Commission Costs')
        axes[0, 0].set_ylabel('Commission ($)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Commission rate over time
        axes[0, 1].plot(daily_df['date'], daily_df['commission_bps'], marker='o')
        axes[0, 1].set_title('Commission Rate (bps) Over Time')
        axes[0, 1].set_ylabel('Commission Rate (bps)')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Commission by ticker
        ticker_comm = trades_df.groupby('ticker')['commission'].sum().sort_values(ascending=True)
        axes[1, 0].barh(ticker_comm.index, ticker_comm.values)
        axes[1, 0].set_title('Total Commission by Ticker')
        axes[1, 0].set_xlabel('Commission ($)')
        
        # Commission distribution
        axes[1, 1].hist(trades_df['commission'], bins=20, alpha=0.7)
        axes[1, 1].set_title('Commission Distribution per Trade')
        axes[1, 1].set_xlabel('Commission ($)')
        axes[1, 1].set_ylabel('Frequency')
        
        plt.tight_layout()
        plt.savefig('results/transaction_cost_analysis.png', dpi=300, bbox_inches='tight')
        print(f"\n📊 Chart saved to: results/transaction_cost_analysis.png")
    
    def compare_with_backtest(self, actual_bps):
        """Compare actual costs with backtest assumptions"""
        backtest_bps = 1.0  # From backtest
        
        print(f"\n🔍 COST COMPARISON:")
        print("-" * 30)
        print(f"Backtest Assumption: {backtest_bps} bps")
        print(f"Actual Average: {actual_bps:.1f} bps")
        
        if actual_bps > backtest_bps:
            print(f"⚠️  Actual costs are {(actual_bps/backtest_bps - 1)*100:.1f}% higher than backtest")
        else:
            print(f"✅ Actual costs are {(1 - actual_bps/backtest_bps)*100:.1f}% lower than backtest")


def main():
    """Main function to run transaction cost analysis"""
    print("📊 TRANSACTION COST ANALYZER")
    print("="*50)
    
    analyzer = TransactionCostAnalyzer()
    
    try:
        trades_df, daily_df = analyzer.analyze_costs()
        
        if not trades_df.empty:
            # Create visualizations
            analyzer.plot_costs(trades_df, daily_df)
            
            # Compare with backtest
            total_commission = trades_df['commission'].sum()
            total_value = (trades_df['quantity'] * trades_df['fill_price']).abs().sum()
            actual_bps = (total_commission / total_value * 10000) if total_value > 0 else 0
            analyzer.compare_with_backtest(actual_bps)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 
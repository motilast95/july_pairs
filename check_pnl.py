import pandas as pd

# Load the trades data
df = pd.read_csv('results/data/trades_data.csv')

# Calculate total P&L
total_pnl = df['net_pnl'].sum()
print(f"Total P&L: ${total_pnl:.2f}")
print(f"Number of trades: {len(df)}")
print(f"Average P&L per trade: ${df['net_pnl'].mean():.2f}")

# Check the benchmark data
import json
with open('results/benchmark_comparison.json', 'r') as f:
    benchmark_data = json.load(f)

print(f"\nStrategy total return from benchmark data: {benchmark_data['strategy']['total_return']*100:.2f}%")
print(f"Strategy annualized return: {benchmark_data['strategy']['annualized_return']*100:.2f}%") 
"""
Daily Trade Executor for Pairs Trading
Runs at 9:30 AM daily to execute yesterday's signals
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from ib_insync import *
import os
import glob

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DailyTradeExecutor:
    """Execute daily trades based on yesterday's signals"""
    
    def __init__(self, signal_file=None):
        """
        Initialize trade executor
        
        Args:
            signal_file: Path to signal JSON file (if None, finds yesterday's)
        """
        self.signal_file = signal_file
        self.results_dir = "results/live_trading/executions"
        
        # Create results directory if it doesn't exist
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Load signals
        self.load_signals()
        
    def load_signals(self):
        """Load signals from file"""
        try:
            if self.signal_file is None:
                # Find yesterday's signal file
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
                signal_pattern = f"results/live_trading/signals/signals_{yesterday}.json"
                
                if not os.path.exists(signal_pattern):
                    raise FileNotFoundError(f"No signal file found for {yesterday}")
                
                self.signal_file = signal_pattern
            
            # Check if file exists
            if not os.path.exists(self.signal_file):
                raise FileNotFoundError(f"Signal file not found: {self.signal_file}")
            
            with open(self.signal_file, 'r') as f:
                self.signals_data = json.load(f)
            
            logger.info(f"✅ Loaded signals from: {self.signal_file}")
            logger.info(f"📅 Signal date: {self.signals_data['date']}")
            
        except Exception as e:
            logger.error(f"❌ Error loading signals: {e}")
            raise
    
    def get_current_positions(self):
        """Get current portfolio positions"""
        ib = IB()
        try:
            ib.connect('127.0.0.1', 7497, clientId=1)
            logger.info("✅ Connected to IBKR")
            
            # Get current positions
            positions = ib.positions()
            current_positions = {}
            
            for position in positions:
                symbol = position.contract.symbol
                quantity = position.position
                current_positions[symbol] = quantity
                logger.info(f"📊 Current position: {symbol} = {quantity}")
            
            ib.disconnect()
            logger.info("🔌 Disconnected from IBKR")
            
            return current_positions
            
        except Exception as e:
            logger.error(f"❌ Error getting positions: {e}")
            if ib.isConnected():
                ib.disconnect()
            raise
    
    def calculate_trade_orders(self, current_positions):
        """Calculate what trades to execute based on signals"""
        trade_orders = []
        
        # Position sizing parameters (scaled for $1M capital)
        initial_capital = 1000000  # $1M capital
        position_size = 14  # Dollar PnL per 1 spread point (from backtest)
        transaction_cost_bps = 1.0  # Transaction costs (from backtest)
        
        for pair_key, signal_data in self.signals_data['signals'].items():
            signal = signal_data['signal']
            ticker1 = signal_data['ticker1']
            ticker2 = signal_data['ticker2']
            price1 = signal_data['price1']
            price2 = signal_data['price2']
            
            # Get current positions
            pos1 = current_positions.get(ticker1, 0)
            pos2 = current_positions.get(ticker2, 0)
            
            logger.info(f"📊 {pair_key}: Signal={signal}, Current: {ticker1}={pos1}, {ticker2}={pos2}")
            
            # Calculate position sizes based on dollar allocation
            if signal in ["LONG", "SHORT"]:
                # Calculate dollar allocation per pair (simple scaling from backtest)
                # Backtest used $14 per spread point, scale to $1M capital
                pair_allocation = initial_capital * 0.1  # 10% per pair = $100k
                
                # Calculate shares based on price and allocation
                # For pairs trading, we want equal dollar exposure on both sides
                shares1 = int(pair_allocation / (2 * price1))  # Half allocation to each stock
                shares2 = int(pair_allocation / (2 * price2))
                
                # Ensure minimum position size
                min_shares = 100
                shares1 = max(shares1, min_shares)
                shares2 = max(shares2, min_shares)
                
                if signal == "LONG":
                    # Long the spread: Long ticker1, Short ticker2
                    target_pos1 = shares1
                    target_pos2 = -shares2
                    
                elif signal == "SHORT":
                    # Short the spread: Short ticker1, Long ticker2
                    target_pos1 = -shares1
                    target_pos2 = shares2
                    
            elif signal == "FLAT":
                # Close positions
                target_pos1 = 0
                target_pos2 = 0
                
            else:  # HOLD
                # No change
                target_pos1 = pos1
                target_pos2 = pos2
            
            # Calculate required trades
            if target_pos1 != pos1:
                trade_orders.append({
                    'ticker': ticker1,
                    'action': 'BUY' if target_pos1 > pos1 else 'SELL',
                    'quantity': abs(target_pos1 - pos1),
                    'pair': pair_key,
                    'signal': signal,
                    'price': price1,
                    'dollar_value': abs(target_pos1 - pos1) * price1
                })
            
            if target_pos2 != pos2:
                trade_orders.append({
                    'ticker': ticker2,
                    'action': 'BUY' if target_pos2 > pos2 else 'SELL',
                    'quantity': abs(target_pos2 - pos2),
                    'pair': pair_key,
                    'signal': signal,
                    'price': price2,
                    'dollar_value': abs(target_pos2 - pos2) * price2
                })
        
        return trade_orders
    
    def execute_trades(self, trade_orders):
        """Execute trades via IBKR"""
        if not trade_orders:
            logger.info("📊 No trades to execute")
            return []
        
        ib = IB()
        try:
            ib.connect('127.0.0.1', 7497, clientId=1)
            logger.info("✅ Connected to IBKR for trading")
            
            executed_trades = []
            total_commission = 0.0
            
            for order in trade_orders:
                ticker = order['ticker']
                action = order['action']
                quantity = order['quantity']
                
                logger.info(f"📈 Executing: {action} {quantity} {ticker}")
                
                # Create contract
                contract = Stock(ticker, 'SMART', 'USD')
                ib.qualifyContracts(contract)
                
                # Create order
                if action == 'BUY':
                    order_obj = MarketOrder('BUY', quantity)
                else:
                    order_obj = MarketOrder('SELL', quantity)
                
                # Submit order
                trade = ib.placeOrder(contract, order_obj)
                
                # Wait for order to be filled
                ib.sleep(2)
                
                # Check order status
                if trade.orderStatus.status == 'Filled':
                    # Get commission from fills
                    commission = 0.0
                    if trade.fills:
                        for fill in trade.fills:
                            if hasattr(fill, 'commissionReport') and fill.commissionReport:
                                commission += fill.commissionReport.commission
                    
                    total_commission += commission
                    
                    executed_trades.append({
                        'ticker': ticker,
                        'action': action,
                        'quantity': quantity,
                        'fill_price': trade.orderStatus.avgFillPrice,
                        'commission': commission,
                        'status': 'Filled',
                        'pair': order['pair'],
                        'signal': order['signal']
                    })
                    logger.info(f"✅ Filled: {action} {quantity} {ticker} @ ${trade.orderStatus.avgFillPrice:.2f} (Commission: ${commission:.2f})")
                else:
                    logger.warning(f"⚠️ Order not filled: {action} {quantity} {ticker} - Status: {trade.orderStatus.status}")
            
            logger.info(f"💰 Total commission for this session: ${total_commission:.2f}")
            ib.disconnect()
            logger.info("🔌 Disconnected from IBKR")
            
            return executed_trades
            
        except Exception as e:
            logger.error(f"❌ Error executing trades: {e}")
            if ib.isConnected():
                ib.disconnect()
            raise
    
    def save_execution_results(self, executed_trades):
        """Save execution results to file"""
        today = datetime.now().strftime('%Y%m%d')
        result_file = f"{self.results_dir}/execution_{today}.json"
        
        # Calculate total commission
        total_commission = sum(trade.get('commission', 0) for trade in executed_trades)
        total_value = sum(abs(trade['quantity'] * trade['fill_price']) for trade in executed_trades)
        
        execution_data = {
            'date': today,
            'executed_at': datetime.now().isoformat(),
            'signal_file': self.signal_file,
            'executed_trades': executed_trades,
            'total_trades': len(executed_trades),
            'total_commission': total_commission,
            'total_trade_value': total_value,
            'commission_bps': (total_commission / total_value * 10000) if total_value > 0 else 0
        }
        
        with open(result_file, 'w') as f:
            json.dump(execution_data, f, indent=2)
        
        logger.info(f"💾 Saved execution results to: {result_file}")
        return result_file
    
    def run_daily_execution(self):
        """Run the complete daily execution process"""
        logger.info("🚀 Starting daily trade execution...")
        
        try:
            # Step 1: Get current positions
            logger.info("📊 Step 1: Getting current positions...")
            current_positions = self.get_current_positions()
            
            # Step 2: Calculate trade orders
            logger.info("🧮 Step 2: Calculating trade orders...")
            trade_orders = self.calculate_trade_orders(current_positions)
            
            # Step 3: Execute trades
            logger.info("📈 Step 3: Executing trades...")
            executed_trades = self.execute_trades(trade_orders)
            
            # Step 4: Save results
            logger.info("💾 Step 4: Saving execution results...")
            result_file = self.save_execution_results(executed_trades)
            
            # Summary
            logger.info("✅ Daily execution complete!")
            logger.info(f"📁 Results saved to: {result_file}")
            
            # Print summary
            self.print_summary(executed_trades)
            
            return result_file
            
        except Exception as e:
            logger.error(f"❌ Error in daily execution: {e}")
            raise
    
    def print_summary(self, executed_trades):
        """Print a summary of executed trades"""
        print("\n" + "="*50)
        print("📊 DAILY EXECUTION SUMMARY")
        print("="*50)
        
        if not executed_trades:
            print("📊 No trades executed today")
        else:
            total_value = 0
            total_commission = 0
            for trade in executed_trades:
                value = trade['quantity'] * trade['fill_price']
                commission = trade.get('commission', 0)
                total_value += abs(value)
                total_commission += commission
                print(f"📈 {trade['action']} {trade['quantity']} {trade['ticker']} @ ${trade['fill_price']:.2f} (Commission: ${commission:.2f}) ({trade['pair']})")
            
            commission_bps = (total_commission / total_value * 10000) if total_value > 0 else 0
            print(f"\n💰 Total trade value: ${total_value:,.2f}")
            print(f"💸 Total commission: ${total_commission:.2f}")
            print(f"📊 Commission rate: {commission_bps:.1f} bps")
            print(f"📊 Total trades: {len(executed_trades)}")
        
        print("="*50)


def main():
    """Main function to run daily trade execution"""
    print("🚀 DAILY TRADE EXECUTOR")
    print("="*50)
    
    try:
        # Check for command line argument
        import sys
        signal_file = None
        if len(sys.argv) > 1:
            signal_file = sys.argv[1]
            print(f"📁 Using signal file: {signal_file}")
        
        # Create trade executor
        executor = DailyTradeExecutor(signal_file)
        
        # Run daily execution
        result_file = executor.run_daily_execution()
        
        print(f"\n✅ Success! Execution results saved to: {result_file}")
        print("📅 Ready for next day's signals at 5:00 PM")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 
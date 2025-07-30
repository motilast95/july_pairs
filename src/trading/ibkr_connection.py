"""
IBKR Connection Module
Simple connection test for Interactive Brokers paper trading
"""

import logging
from ib_insync import *
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IBKRConnection:
    """Simple IBKR connection class for testing"""
    
    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        """
        Initialize IBKR connection
        
        Args:
            host: TWS/Gateway host (default: 127.0.0.1 for local)
            port: Port number (7497 for paper trading, 7496 for live)
            client_id: Unique client ID
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.connected = False
        
    def connect(self):
        """Connect to IBKR TWS/Gateway"""
        try:
            logger.info(f"Attempting to connect to IBKR at {self.host}:{self.port}")
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            
            # Wait a moment for connection to establish
            time.sleep(2)
            
            if self.ib.isConnected():
                self.connected = True
                logger.info("✅ Successfully connected to IBKR!")
                
                # Get account info
                accounts = self.ib.managedAccounts()
                if accounts:
                    logger.info(f"📊 Connected to account: {accounts[0]}")
                else:
                    logger.warning("⚠️ No managed accounts found")
                    
                return True
            else:
                logger.error("❌ Failed to connect to IBKR")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection error: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("🔌 Disconnected from IBKR")
    
    def get_account_info(self):
        """Get basic account information"""
        if not self.connected:
            logger.error("❌ Not connected to IBKR")
            return None
            
        try:
            # Get account summary
            account = self.ib.managedAccounts()[0] if self.ib.managedAccounts() else None
            if account:
                logger.info(f"📈 Account: {account}")
                
                # Get account value
                account_values = self.ib.accountSummary()
                for value in account_values:
                    if value.tag == 'NetLiquidation':
                        logger.info(f"💰 Net Liquidation: ${float(value.value):,.2f}")
                    elif value.tag == 'AvailableFunds':
                        logger.info(f"💵 Available Funds: ${float(value.value):,.2f}")
                        
                return account_values
            else:
                logger.warning("⚠️ No account information available")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting account info: {str(e)}")
            return None
    
    def test_connection(self):
        """Run a complete connection test"""
        logger.info("🚀 Starting IBKR connection test...")
        
        # Try to connect
        if self.connect():
            # Get account info
            self.get_account_info()
            
            # Disconnect
            self.disconnect()
            logger.info("✅ Connection test completed successfully!")
            return True
        else:
            logger.error("❌ Connection test failed!")
            return False


def main():
    """Simple test function"""
    print("=" * 50)
    print("IBKR PAPER TRADING CONNECTION TEST")
    print("=" * 50)
    
    # Create connection (paper trading settings)
    connection = IBKRConnection(
        host='127.0.0.1',  # Local TWS/Gateway
        port=7497,          # Paper trading port
        client_id=1         # Unique client ID
    )
    
    # Run the test
    success = connection.test_connection()
    
    if success:
        print("\n🎉 CONNECTION SUCCESSFUL!")
        print("Your IBKR paper trading account is ready for integration.")
    else:
        print("\n❌ CONNECTION FAILED!")
        print("Please check:")
        print("1. Is TWS or IB Gateway running?")
        print("2. Is it configured for paper trading?")
        print("3. Are the connection settings correct?")
    
    print("=" * 50)


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Universe Manager for handling different trading universes.
Supports mega-cap, mid-cap, and custom universes with sector groupings.
"""

import yfinance as yf
import pandas as pd
from typing import List, Dict

class UniverseManager:
    def __init__(self):
        # Mega-cap universe (current default) - matches legacy CSV
        self.mega_cap_tickers = [
            'AAPL', 'ABBV', 'ABT', 'ADBE', 'AMGN', 'AMZN', 'AVGO', 'AXP', 'BA', 'BAC',
            'BK', 'BKR', 'BMY', 'C', 'CAT', 'COP', 'CSCO', 'CVX', 'DE', 'EOG',
            'F', 'GE', 'GM', 'GOOGL', 'GS', 'HAL', 'HD', 'HON', 'INTC', 'JNJ',
            'JPM', 'LLY', 'LMT', 'LOW', 'MCD', 'META', 'MMM', 'MPC', 'MRK', 'MS',
            'MSFT', 'NKE', 'NVDA', 'ORCL', 'PFE', 'PSX', 'RTX', 'SBUX', 'SCHW', 'SLB',
            'TGT', 'TJX', 'TMO', 'UNH', 'UNP', 'UPS', 'USB', 'VLO', 'WFC', 'XOM'
        ]
        
        # Mid-cap universe (sample of liquid mid-caps)
        self.mid_cap_tickers = [
            # Technology (well-established)
            'ETSY', 'SNAP', 'PINS', 'ZM', 'RBLX', 'PLTR', 'SNOW', 'DDOG',
            'NET', 'CRWD', 'ZS', 'OKTA', 'TEAM', 'DOCU', 'PATH', 'U', 'ASAN',
            
            # Consumer/Entertainment
            'ROKU', 'SPOT', 'UBER', 'LYFT', 'DASH', 'ABNB', 'PTON', 'FVRR',
            
            # Automotive
            'RIVN', 'LCID', 'NIO', 'XPEV', 'LI',
            
            # International (more stable)
            'MELI', 'SE', 'JD', 'BIDU', 'TME', 'BABA', 'PDD', 'TCEHY'
        ]
    
    def get_universe_tickers(self, universe: str) -> List[str]:
        """Get tickers for a specific universe."""
        if universe == 'mega_cap':
            return self.mega_cap_tickers
        elif universe == 'mid_cap':
            return self.mid_cap_tickers
        elif universe == 'custom':
            # For custom universe, could load from file or accept as parameter
            return self.mega_cap_tickers  # Default to mega-cap for now
        else:
            raise ValueError(f"Unknown universe: {universe}")
    
    def get_universe_sectors(self, universe: str) -> Dict[str, List[str]]:
        """Get sector groupings for a specific universe."""
        if universe == 'mega_cap':
            return self.get_mega_cap_sectors()
        elif universe == 'mid_cap':
            return self.get_mid_cap_sectors()
        elif universe == 'custom':
            return self.get_mega_cap_sectors()  # Default to mega-cap sectors
        else:
            raise ValueError(f"Unknown universe: {universe}")
    
    def get_mega_cap_sectors(self) -> Dict[str, List[str]]:
        """Get sector groupings for mega-cap universe."""
        return {
            'technology': ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'ORCL', 'AVGO', 'ADBE', 'CSCO', 'INTC'],
            'financials': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'SCHW', 'BK', 'AXP', 'USB'],
            'consumer_discretionary': ['AMZN', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TJX', 'TGT', 'GM', 'F'],
            'healthcare': ['JNJ', 'UNH', 'PFE', 'MRK', 'ABBV', 'ABT', 'LLY', 'BMY', 'TMO', 'AMGN'],
            'industrials': ['CAT', 'DE', 'HON', 'UNP', 'UPS', 'BA', 'GE', 'LMT', 'RTX', 'MMM'],
            'energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'BKR', 'HAL']
        }
    
    def get_mid_cap_sectors(self) -> Dict[str, List[str]]:
        """Get sector groupings for mid-cap universe."""
        return {
            'technology': ['ETSY', 'SNAP', 'PINS', 'ZM', 'RBLX', 'PLTR', 'SNOW', 'DDOG', 'NET', 'CRWD', 'ZS', 'OKTA', 'TEAM', 'DOCU', 'PATH', 'U', 'ASAN'],
            'consumer': ['ROKU', 'SPOT', 'UBER', 'LYFT', 'DASH', 'ABNB', 'PTON', 'FVRR'],
            'automotive': ['RIVN', 'LCID', 'NIO', 'XPEV', 'LI'],
            'international': ['MELI', 'SE', 'JD', 'BIDU', 'TME', 'BABA', 'PDD', 'TCEHY']
        }
    
    def get_universe_parameters(self, universe: str) -> Dict:
        """Get universe-specific parameters (transaction costs, position sizes, etc.)."""
        if universe == 'mega_cap':
            return {
                'transaction_cost_bps': 1.0,
                'position_size': 100.0,
                'distance_threshold': 0.1,
                'min_volume': 1000000  # 1M shares daily
            }
        elif universe == 'mid_cap':
            return {
                'transaction_cost_bps': 2.5,
                'position_size': 50.0,
                'distance_threshold': 0.15,  # Slightly higher for mid-caps
                'min_volume': 500000  # 500K shares daily
            }
        else:
            return {
                'transaction_cost_bps': 1.0,
                'position_size': 100.0,
                'distance_threshold': 0.1,
                'min_volume': 1000000
            } 
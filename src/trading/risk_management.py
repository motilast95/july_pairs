"""
Risk management module for the pairs trading system.
Handles portfolio-level risk controls and position sizing.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class PortfolioRiskManager:
    """Manages portfolio-level risk controls for pairs trading."""
    
    def __init__(self, config: Dict):
        """
        Initialize risk manager with configuration.
        
        Args:
            config: Configuration dictionary with risk parameters
        """
        self.max_position_per_pair = config.get('max_position_per_pair', 1.0)
        self.max_portfolio_exposure = config.get('max_portfolio_exposure', 0.5)
        self.volatility_lookback = config.get('volatility_lookback', 252)
        self.volatility_target = config.get('volatility_target', 0.15)  # 15% annual volatility target
        # New toggles and thresholds
        self.enable_volatility_scaling = config.get('enable_volatility_scaling', True)
        self.enable_position_limits = config.get('enable_position_limits', True)
        self.enable_pair_validation = config.get('enable_pair_validation', True)
        self.max_pair_volatility = config.get('max_pair_volatility', 0.5)
        self.max_daily_move = config.get('max_daily_move', 0.2)
        self.min_data_days = config.get('min_data_days', 60)

    def calculate_volatility_scaled_position(
        self, 
        position: float, 
        pair_volatility: float,
        portfolio_volatility: float
    ) -> float:
        """
        Scale position based on volatility.
        """
        if not self.enable_volatility_scaling:
            return position
        if pair_volatility == 0:
            return 0.0
        vol_scale = min(1.0, self.volatility_target / pair_volatility)
        portfolio_scale = min(1.0, self.volatility_target / portfolio_volatility) if portfolio_volatility > 0 else 1.0
        scaled_position = position * vol_scale * portfolio_scale
        if self.enable_position_limits:
            scaled_position = np.clip(scaled_position, -self.max_position_per_pair, self.max_position_per_pair)
        return scaled_position
    
    def calculate_portfolio_volatility(
        self, 
        positions: pd.DataFrame, 
        returns: pd.DataFrame
    ) -> pd.Series:
        """
        Calculate rolling portfolio volatility.
        
        Args:
            positions: DataFrame of positions (pairs x dates)
            returns: DataFrame of returns (pairs x dates)
            
        Returns:
            Series of portfolio volatility over time
        """
        if positions.empty or returns.empty:
            return pd.Series(dtype=float)
        
        # Calculate portfolio returns
        portfolio_returns = (positions * returns).sum(axis=1)
        
        # Calculate rolling volatility
        portfolio_vol = portfolio_returns.rolling(
            window=self.volatility_lookback, 
            min_periods=self.volatility_lookback
        ).std() * np.sqrt(252)  # Annualize
        
        return portfolio_vol
    
    def apply_position_limits(
        self, 
        positions: pd.DataFrame,
        current_exposure: float = 0.0
    ) -> pd.DataFrame:
        """
        Apply position limits to ensure portfolio constraints are met.
        """
        if not self.enable_position_limits:
            return positions
        total_exposure = positions.abs().sum(axis=1)
        max_allowed_exposure = self.max_portfolio_exposure
        scaling_factor = np.where(
            total_exposure > max_allowed_exposure,
            max_allowed_exposure / total_exposure,
            1.0
        )
        adjusted_positions = positions * scaling_factor[:, np.newaxis]
        return adjusted_positions
    
    def calculate_correlation_penalty(
        self, 
        pair: Tuple[str, str], 
        existing_pairs: List[Tuple[str, str]], 
        prices: pd.DataFrame,
        lookback: int = 252
    ) -> float:
        """
        Calculate correlation penalty for adding a new pair.
        
        Args:
            pair: New pair to evaluate
            existing_pairs: List of currently active pairs
            prices: Price data
            lookback: Lookback period for correlation calculation
            
        Returns:
            Correlation penalty factor (0-1, where 1 = no penalty)
        """
        if not existing_pairs:
            return 1.0
        
        try:
            # Calculate returns for new pair
            pair_prices = prices.loc[:, list(pair)].dropna()
            if len(pair_prices) < lookback:
                return 0.5  # Penalty for insufficient data
            
            pair_returns = pair_prices.pct_change().dropna()
            pair_spread_returns = pair_returns.iloc[:, 0] - pair_returns.iloc[:, 1]
            
            # Calculate correlations with existing pairs
            max_correlation = 0.0
            for existing_pair in existing_pairs:
                existing_prices = prices.loc[:, list(existing_pair)].dropna()
                if len(existing_prices) < lookback:
                    continue
                
                existing_returns = existing_prices.pct_change().dropna()
                existing_spread_returns = existing_returns.iloc[:, 0] - existing_returns.iloc[:, 1]
                
                # Align time periods
                common_idx = pair_spread_returns.index.intersection(existing_spread_returns.index)
                if len(common_idx) < lookback // 2:
                    continue
                
                correlation = abs(pair_spread_returns.loc[common_idx].corr(existing_spread_returns.loc[common_idx]))
                max_correlation = max(max_correlation, correlation)
            
            # Calculate penalty (higher correlation = higher penalty)
            penalty = max(0.1, 1.0 - max_correlation)
            return penalty
            
        except Exception as e:
            logger.warning(f"Error calculating correlation penalty for {pair}: {e}")
            return 0.5  # Default penalty
    
    def validate_pair_risk(
        self, 
        pair: Tuple[str, str], 
        prices: pd.DataFrame, 
        window: slice
    ) -> bool:
        """
        Validate if a pair meets risk criteria.
        """
        if not self.enable_pair_validation:
            return True
        try:
            x, y = pair
            pair_prices = prices.loc[window, [x, y]].dropna()
            if len(pair_prices) < self.min_data_days:
                logger.debug(f"Pair {pair} rejected: insufficient data ({len(pair_prices)} days < {self.min_data_days})")
                return False
            spread = pair_prices[x] - pair_prices[y]
            spread_vol = spread.pct_change().std() * np.sqrt(252)
            if spread_vol > self.max_pair_volatility:
                logger.debug(f"Pair {pair} rejected: high volatility {spread_vol:.2%} > {self.max_pair_volatility:.2%}")
                return False
            price_changes = pair_prices.pct_change().abs()
            if price_changes.max().max() > self.max_daily_move:
                logger.debug(f"Pair {pair} rejected: extreme price movements {price_changes.max().max():.2%} > {self.max_daily_move:.2%}")
                return False
            return True
        except Exception as e:
            logger.warning(f"Error validating pair {pair}: {e}")
            return False


def calculate_drawdown_limits(
    cumulative_returns: pd.Series, 
    max_drawdown_threshold: float = 0.15
) -> pd.Series:
    """
    Calculate position scaling based on drawdown limits.
    
    Args:
        cumulative_returns: Cumulative portfolio returns
        max_drawdown_threshold: Maximum allowed drawdown (e.g., 0.15 = 15%)
        
    Returns:
        Series of position scaling factors
    """
    # Calculate running maximum
    running_max = cumulative_returns.cummax()
    
    # Calculate current drawdown
    drawdown = (cumulative_returns - running_max) / running_max
    
    # Calculate scaling factor (reduce positions as drawdown approaches limit)
    scaling_factor = np.where(
        drawdown > -max_drawdown_threshold,
        1.0 + (drawdown / max_drawdown_threshold),  # Scale down as drawdown increases
        0.0  # Stop trading if drawdown exceeds limit
    )
    
    # Ensure scaling factor is between 0 and 1
    scaling_factor = np.clip(scaling_factor, 0.0, 1.0)
    
    return pd.Series(scaling_factor, index=cumulative_returns.index)


def calculate_var_position_limit(
    positions: pd.DataFrame, 
    returns: pd.DataFrame, 
    confidence_level: float = 0.95,
    var_window: int = 252
) -> pd.Series:
    """
    Calculate position limits based on Value at Risk (VaR).
    
    Args:
        positions: Current positions
        returns: Historical returns
        confidence_level: VaR confidence level (e.g., 0.95 for 95%)
        var_window: Window for VaR calculation
        
    Returns:
        Series of position scaling factors
    """
    if positions.empty or returns.empty:
        return pd.Series(1.0, index=positions.index if not positions.empty else pd.DatetimeIndex([]))
    
    # Calculate portfolio returns
    portfolio_returns = (positions * returns).sum(axis=1)
    
    # Calculate rolling VaR
    var_series = pd.Series(index=portfolio_returns.index, dtype=float)
    
    for i in range(var_window, len(portfolio_returns)):
        window_returns = portfolio_returns.iloc[i-var_window:i]
        var = np.percentile(window_returns, (1 - confidence_level) * 100)
        var_series.iloc[i] = abs(var)
    
    # Calculate position scaling based on VaR
    # Higher VaR = lower position scaling
    max_var = var_series.quantile(0.9)  # 90th percentile as reference
    scaling_factor = np.where(
        var_series > 0,
        max_var / var_series,
        1.0
    )
    
    # Ensure scaling factor is between 0.1 and 1.0
    scaling_factor = np.clip(scaling_factor, 0.1, 1.0)
    
    return scaling_factor 
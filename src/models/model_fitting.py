from typing import Tuple, Dict, Optional
import pandas as pd
import numpy as np
import logging
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

# Set up logging
logger = logging.getLogger(__name__)

def fit_spread(pair: Tuple[str, str], prices: pd.DataFrame, window: slice) -> Optional[Dict]:
    """
    Fit a linear regression model to estimate the hedge ratio (beta) for the pair in the given window.
    
    Args:
        pair: Tuple of (ticker1, ticker2) for the pair
        prices: DataFrame with price data
        window: Slice object defining the time window
        
    Returns:
        Dict with beta, spread, mean, std, and model summary, or None if fitting fails
        
    Raises:
        ValueError: If inputs are invalid
    """
    try:
        # Input validation
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError("Pair must be a tuple of exactly 2 tickers")
        
        x, y = pair
        if x not in prices.columns or y not in prices.columns:
            raise ValueError(f"Tickers {pair} not found in price data")
        
        # Extract window data
        window_prices = prices.loc[window, [x, y]].dropna()
        
        # Check data sufficiency
        if window_prices.shape[0] < 30:  # Minimum 30 observations
            logger.warning(f"Insufficient data for pair {pair}: {window_prices.shape[0]} observations")
            return None
        
        # Check for constant prices (no variation)
        if window_prices[x].std() == 0 or window_prices[y].std() == 0:
            logger.warning(f"Constant prices detected for pair {pair}")
            return None
        
        # Fit regression model
        X = add_constant(window_prices[y])
        model = OLS(window_prices[x], X).fit()
        
        # Validate model fit
        if model.rsquared < 0.1:  # R-squared threshold
            logger.warning(f"Poor model fit for pair {pair}: R² = {model.rsquared:.3f}")
            return None
        
        beta = model.params[y]
        spread = window_prices[x] - beta * window_prices[y]
        spread_mean = spread.mean()
        spread_std = spread.std()
        
        # Check for reasonable spread statistics
        if spread_std == 0 or np.isnan(spread_std):
            logger.warning(f"Invalid spread statistics for pair {pair}")
            return None
        
        logger.debug(f"Successfully fitted model for pair {pair}: beta={beta:.4f}, R²={model.rsquared:.3f}")
        
        return {
            'beta': beta,
            'spread_mean': spread_mean,
            'spread_std': spread_std,
            'spread': spread,
            'rsquared': model.rsquared,
            'model_summary': model.summary().as_text()
        }
        
    except Exception as e:
        logger.error(f"Error fitting model for pair {pair}: {str(e)}")
        return None 
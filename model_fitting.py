from typing import Tuple, Dict
import pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

def fit_spread(pair: Tuple[str, str], prices: pd.DataFrame, window: slice) -> Dict:
    """
    Fit a linear regression model to estimate the hedge ratio (beta) for the pair in the given window.
    Returns a dict with beta, spread, mean, std, and model summary.
    """
    x, y = pair
    window_prices = prices.loc[window, [x, y]].dropna()
    if window_prices.shape[0] < 2:
        return {}
    X = add_constant(window_prices[y])
    model = OLS(window_prices[x], X).fit()
    beta = model.params[y]
    spread = window_prices[x] - beta * window_prices[y]
    spread_mean = spread.mean()
    spread_std = spread.std()
    return {
        'beta': beta,
        'spread_mean': spread_mean,
        'spread_std': spread_std,
        'spread': spread,
        'model_summary': model.summary().as_text()
    } 
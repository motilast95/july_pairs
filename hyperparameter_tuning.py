# from typing import Tuple, Dict
# import pandas as pd
# import numpy as np

# def simulate_trades(spread, entry_z, exit_z, mean, std):
#     """Simulate simple long/short trades on the spread using z-score thresholds."""
#     zscores = (spread - mean) / std
#     position = 0  # 1 for long, -1 for short, 0 for flat
#     pnl = []
#     for z in zscores:
#         if position == 0:
#             if z < -entry_z:
#                 position = 1  # long spread
#             elif z > entry_z:
#                 position = -1  # short spread
#         elif position == 1 and z > -exit_z:
#             position = 0  # exit long
#         elif position == -1 and z < exit_z:
#             position = 0  # exit short
#         pnl.append(position)
#     # Calculate returns as change in spread * position
#     returns = np.diff(spread) * np.array(pnl[:-1])
#     return returns

# def tune_hyperparameters(pair: Tuple[str, str], prices: pd.DataFrame, window: slice, model_params: Dict) -> Dict:
#     """
#     Tune entry/exit z-score thresholds using the validation window.
#     Returns the best hyperparameters based on total return.
#     """
#     spread = model_params['spread'].loc[window]
#     mean = model_params['spread_mean']
#     std = model_params['spread_std']
#     best_score = -np.inf
#     best_params = {}
#     for entry_z in [1.0, 1.5, 2.0]:
#         for exit_z in [0.0, 0.5]:
#             returns = simulate_trades(spread, entry_z, exit_z, mean, std)
#             score = returns.sum()  # total return
#             if score > best_score:
#                 best_score = score
#                 best_params = {'entry_z': entry_z, 'exit_z': exit_z, 'total_return': score}
#     return best_params
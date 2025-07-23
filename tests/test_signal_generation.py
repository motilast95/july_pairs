import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
from signal_generation import generate_signals, generate_rolling_scaled_signals

def test_generate_signals_basic():
    spread = pd.Series([0, 1, 2, 1, 0, -1, -2, -1, 0])
    mean = spread.mean()
    std = spread.std()
    entry_z = 1.0
    exit_z = 0.5
    signals = generate_signals(spread, mean, std, entry_z, exit_z)
    assert isinstance(signals, pd.Series)
    assert set(signals.unique()).issubset({-1, 0, 1})

def test_generate_rolling_scaled_signals_basic():
    spread = pd.Series([0, 1, 2, 1, 0, -1, -2, -1, 0], dtype=float)
    rolling_window = 3
    entry_z = 1.0
    exit_z = 0.5
    positions = generate_rolling_scaled_signals(
        spread,
        entry_z=entry_z,
        exit_z=exit_z,
        rolling_window=rolling_window
    )
    assert isinstance(positions, pd.Series)
    zscores = (spread - spread.rolling(rolling_window, min_periods=rolling_window).mean()) / spread.rolling(rolling_window, min_periods=rolling_window).std()
    # The test logic here is limited since the function is stateful, but we can check that when in a trade, position == -zscore
    # We'll check for the first entry after |z| > entry_z
    entered = False
    for t, z in enumerate(zscores):
        if pd.isna(z):
            continue
        if not entered and abs(z) > entry_z:
            entered = True
        if entered and abs(z) >= exit_z:
            assert np.isclose(positions.iloc[t], -z, equal_nan=True)
    assert positions.shape == spread.shape 
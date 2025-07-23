import pandas as pd
import numpy as np

def generate_signals(
    spread: pd.Series,
    mean: float,
    std: float,
    entry_z: float,
    exit_z: float
) -> pd.Series:
    """
    Generate trading signals based on z-score of the spread.
    1 = long entry, -1 = short entry, 0 = exit/flat.
    """
    zscores = (spread - mean) / std
    signals = pd.Series(0, index=spread.index)
    position = 0  # 0=flat, 1=long, -1=short
    for t, z in enumerate(zscores):
        if position == 0:
            if z < -entry_z:
                position = 1
            elif z > entry_z:
                position = -1
        elif position == 1 and z > -exit_z:
            position = 0
        elif position == -1 and z < exit_z:
            position = 0
        signals.iloc[t] = position
    return signals

def generate_rolling_signals(
    spread: pd.Series,
    entry_z: float,
    exit_z: float,
    rolling_window: int = 60
) -> pd.Series:
    """
    Generate trading signals using rolling mean and std for z-score calculation.
    """
    rolling_mean = spread.rolling(window=rolling_window, min_periods=rolling_window).mean()
    rolling_std = spread.rolling(window=rolling_window, min_periods=rolling_window).std()
    zscores = (spread - rolling_mean) / rolling_std
    signals = pd.Series(0, index=spread.index)
    position = 0
    for t, z in enumerate(zscores):
        if pd.isna(z):
            signals.iloc[t] = 0
            continue
        if position == 0:
            if z < -entry_z:
                position = 1
            elif z > entry_z:
                position = -1
        elif position == 1 and z > -exit_z:
            position = 0
        elif position == -1 and z < exit_z:
            position = 0
        signals.iloc[t] = position
    return signals

def generate_rolling_scaled_signals(
    spread: pd.Series,
    entry_z: float,
    exit_z: float,
    rolling_window: int = 60
) -> pd.Series:
    """
    Generate scaled trading signals using rolling mean and std for z-score calculation.
    Enter when z > entry_z (short) or z < -entry_z (long), scale position with -z-score while in a trade, exit when z crosses the correct exit threshold for the direction.
    """
    rolling_mean = spread.rolling(window=rolling_window, min_periods=rolling_window).mean()
    rolling_std = spread.rolling(window=rolling_window, min_periods=rolling_window).std()
    zscores = (spread - rolling_mean) / rolling_std
    positions = pd.Series(0.0, index=spread.index)
    position = 0  # 0=flat, 1=long, -1=short
    for t, z in enumerate(zscores):
        if pd.isna(z):
            positions.iloc[t] = 0.0
            continue
        if position == 0:
            if z > entry_z:
                position = -1  # short
            elif z < -entry_z:
                position = 1   # long
        elif position == 1:  # long
            if z > -exit_z:
                position = 0
        elif position == -1:  # short
            if z < exit_z:
                position = 0
        positions.iloc[t] = position * abs(z) if position != 0 else 0.0
    return positions

def generate_rolling_stepwise_signals(
    spread: pd.Series,
    entry_z: float,
    exit_z: float,
    step: float = 0.25,
    rolling_window: int = 60
) -> pd.Series:
    """
    Generate stepwise scaled trading signals using rolling mean and std for z-score calculation.
    Position size increases in steps (default 0.25) as z-score moves further from zero.
    Entry/exit logic is stateful as in generate_rolling_scaled_signals.
    """
    rolling_mean = spread.rolling(window=rolling_window, min_periods=rolling_window).mean()
    rolling_std = spread.rolling(window=rolling_window, min_periods=rolling_window).std()
    zscores = (spread - rolling_mean) / rolling_std
    positions = pd.Series(0.0, index=spread.index)
    position = 0  # 0=flat, 1=long, -1=short
    for t, z in enumerate(zscores):
        if pd.isna(z):
            positions.iloc[t] = 0.0
            continue
        if position == 0:
            if z > entry_z:
                position = -1  # short
            elif z < -entry_z:
                position = 1   # long
        elif position == 1:  # long
            if z > -exit_z:
                position = 0
        elif position == -1:  # short
            if z < exit_z:
                position = 0
        # Stepwise scaling
        if position != 0:
            stepwise_z = np.sign(z) * np.ceil(abs(z) / step) * step
            positions.iloc[t] = position * abs(stepwise_z)
        else:
            positions.iloc[t] = 0.0
    return positions

def generate_rolling_stepwise_scaled_signals(
    spread: pd.Series,
    entry_z: float,
    exit_z: float,
    step: float = 0.25,
    rolling_window: int = 60,
    scaling_factor: float = 1.0
) -> pd.Series:
    """
    Generate stepwise scaled trading signals using rolling mean and std for z-score calculation, with an additional scaling factor.
    Position size increases in steps (default 0.25) as z-score moves further from zero, then is multiplied by scaling_factor.
    Entry/exit logic is stateful as in generate_rolling_scaled_signals.
    """
    import numpy as np
    rolling_mean = spread.rolling(window=rolling_window, min_periods=rolling_window).mean()
    rolling_std = spread.rolling(window=rolling_window, min_periods=rolling_window).std()
    zscores = (spread - rolling_mean) / rolling_std
    positions = pd.Series(0.0, index=spread.index)
    position = 0  # 0=flat, 1=long, -1=short
    for t, z in enumerate(zscores):
        if pd.isna(z):
            positions.iloc[t] = 0.0
            continue
        if position == 0:
            if z > entry_z:
                position = -1  # short
            elif z < -entry_z:
                position = 1   # long
        elif position == 1:  # long
            if z > -exit_z:
                position = 0
        elif position == -1:  # short
            if z < exit_z:
                position = 0
        # Stepwise scaling
        if position != 0:
            stepwise_z = np.sign(z) * np.ceil(abs(z) / step) * step
            positions.iloc[t] = scaling_factor * position * abs(stepwise_z)
        else:
            positions.iloc[t] = 0.0
    return positions

def generate_tiered_signals(
    spread: pd.Series,
    entry_z: float = 1.0,
    exit_z: float = 0.5,
    rolling_window: int = 60,
    scaling_factor: float = 1.0
) -> pd.Series:
    """
    Generate tiered position signals based on z-score buckets:
    |z| >= 2   -> 1
    |z| >= 1.5 -> 0.5
    |z| >= 1   -> 0.25
    Otherwise  -> 0
    Exit when |z| < exit_z (default 0.5).
    Direction: long if z < 0, short if z > 0.
    scaling_factor: scales the final position size (default 1.0)
    """
    import numpy as np
    rolling_mean = spread.rolling(window=rolling_window, min_periods=rolling_window).mean()
    rolling_std = spread.rolling(window=rolling_window, min_periods=rolling_window).std()
    zscores = (spread - rolling_mean) / rolling_std
    positions = pd.Series(0.0, index=spread.index)
    position = 0.0  # 0=flat, positive=long, negative=short
    for t, z in enumerate(zscores):
        if pd.isna(z):
            positions.iloc[t] = 0.0
            continue
        abs_z = abs(z)
        # Exit logic
        if position != 0 and abs_z < exit_z:
            position = 0.0
        # Entry/tier logic (only if not flat)
        if position == 0:
            if abs_z >= 2:
                position = 1.0 * np.sign(-z)  # long if z<0, short if z>0
            elif abs_z >= 1.5:
                position = 0.5 * np.sign(-z)
            elif abs_z >= 1:
                position = 0.25 * np.sign(-z)
            else:
                position = 0.0
        else:
            # If in a position, update tier if z moves to a new bucket
            if abs_z >= 2:
                position = 1.0 * np.sign(-z)
            elif abs_z >= 1.5:
                position = 0.5 * np.sign(-z)
            elif abs_z >= 1:
                position = 0.25 * np.sign(-z)
            # else: keep current position until exit
        positions.iloc[t] = scaling_factor * position
    return positions
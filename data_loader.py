import pandas as pd
import importlib.util
import sys
from typing import Dict

def load_prices(filepath: str) -> pd.DataFrame:
    """Load and clean price data from a CSV file."""
    return pd.read_csv(filepath, parse_dates=True, index_col=0)

def load_sector_tickers(config_path: str) -> Dict[str, list]:
    """Dynamically import sector_tickers from a config Python file."""
    spec = importlib.util.spec_from_file_location("data_params", config_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec or loader from {config_path}")
    data_params = importlib.util.module_from_spec(spec)
    sys.modules["data_params"] = data_params
    spec.loader.exec_module(data_params)
    return data_params.sector_tickers 
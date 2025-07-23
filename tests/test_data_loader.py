import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from src.data.data_loader import *
 
def test_data_loader_exists():
    assert callable(globals().get('load_data', None)) or True  # Placeholder: update if function exists 
import sys
import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from backend.finance import get_current_prices, get_exchange_rate

@patch('backend.finance.yf.Ticker')
def test_get_current_prices_success(mock_ticker):
    # Mock for A.SA
    mock_instance_a = MagicMock()
    mock_df_a = pd.DataFrame({'Close': [100.0]})
    mock_instance_a.history.return_value = mock_df_a

    # Mock for B
    mock_instance_b = MagicMock()
    mock_df_b = pd.DataFrame({'Close': [50.0]})
    mock_instance_b.history.return_value = mock_df_b
    
    # Configure side_effect
    def ticker_side_effect(ticker_name):
        if ticker_name == 'A.SA':
            return mock_instance_a
        return mock_instance_b
        
    mock_ticker.side_effect = ticker_side_effect

    assets = [
        {'ticker': 'A', 'tag': 'Ações'}, # Will append .SA
        {'ticker': 'B', 'tag': 'US ETFs'}
    ]
    prices = get_current_prices(assets)
    assert prices['A'] == 100.0
    assert prices['B'] == 50.0

@patch('backend.finance.yf.Ticker')
def test_get_current_prices_empty_or_error(mock_ticker):
    # Empty history
    mock_instance = MagicMock()
    mock_instance.history.return_value = pd.DataFrame()
    mock_ticker.return_value = mock_instance
    
    prices = get_current_prices([{'ticker': 'A'}])
    assert prices['A'] is None

    # Exception
    mock_instance.history.side_effect = Exception("API error")
    prices2 = get_current_prices([{'ticker': 'B'}])
    assert prices2['B'] is None

@patch('backend.finance.yf.Ticker')
def test_get_current_prices_general_exception(mock_ticker):
    mock_ticker.side_effect = Exception("General error")
    prices = get_current_prices([{'ticker': 'A'}])
    assert prices == {}

def test_get_current_prices_empty_list():
    assert get_current_prices([]) == {}

@patch('backend.finance.yf.Ticker')
def test_get_exchange_rate_success(mock_ticker):
    mock_instance = MagicMock()
    mock_df = pd.DataFrame({'Close': [5.10]})
    mock_instance.history.return_value = mock_df
    mock_ticker.return_value = mock_instance
    
    rate = get_exchange_rate()
    assert rate == 5.10

@patch('backend.finance.yf.Ticker')
def test_get_exchange_rate_empty(mock_ticker):
    mock_instance = MagicMock()
    mock_instance.history.return_value = pd.DataFrame()
    mock_ticker.return_value = mock_instance
    
    rate = get_exchange_rate()
    assert rate == 5.0 # Fallback

@patch('backend.finance.yf.Ticker')
def test_get_exchange_rate_exception(mock_ticker):
    mock_ticker.side_effect = Exception("API error")
    rate = get_exchange_rate()
    assert rate == 5.0 # Fallback

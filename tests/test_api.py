import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from finance import get_current_prices

def test_get_current_prices():
    # We will test fetching a known stable ETF/Stock to ensure it returns a dict
    # This might fail if no internet, but good for a basic integration test
    prices = get_current_prices(['VOO'])
    assert 'VOO' in prices
    assert isinstance(prices['VOO'], float) or prices['VOO'] is None

def test_empty_tickers():
    prices = get_current_prices([])
    assert prices == {}

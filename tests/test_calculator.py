import pytest
import sys
import os

# Add backend directory to sys.path to easily import modules for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from backend.calculator import calculate_smart_buy

def test_smart_buy_calculator():
    assets = [
        {'ticker': 'BBOV11.SA', 'quantity': 10, 'average_price': 100, 'nota': 5, 'tag': 'Brazil ETF'},
        {'ticker': 'SMAL11.SA', 'quantity': 10, 'average_price': 100, 'nota': 5, 'tag': 'Brazil ETF'},
        {'ticker': 'VOO', 'quantity': 5, 'average_price': 400, 'nota': 10, 'tag': 'US ETF'}
    ]
    
    current_prices = {
        'BBOV11.SA': 110,  # current value: 1100
        'SMAL11.SA': 90,   # current value: 900
        'VOO': 410         # current value: 2050
    }
    
    # Total BRL current value = 2000
    # Total BRL notas = 10. BBOV11 = 50%, SMAL11 = 50%
    # If we invest 1000 BRL, new total BRL value = 3000
    # Ideal for both = 1500
    # BBOV11 to buy = 1500 - 1100 = 400 BRL
    # SMAL11 to buy = 1500 - 900 = 600 BRL
    
    # USD: VOO current value = 2050
    # Invest 1000 USD
    # VOO to buy = 1000 USD
    
    results = calculate_smart_buy(assets, current_prices, invest_brl=1000, invest_usd=1000)
    
    for r in results:
        if r['ticker'] == 'BBOV11.SA':
            assert r['value_to_buy'] == 400
        elif r['ticker'] == 'SMAL11.SA':
            assert r['value_to_buy'] == 600
        elif r['ticker'] == 'VOO':
            assert r['value_to_buy'] == 1000

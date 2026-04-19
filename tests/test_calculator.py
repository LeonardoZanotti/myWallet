import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from backend.calculator import calculate_smart_buy

def test_smart_buy_proportional_distribution():
    assets = [
        {'ticker': 'A.SA', 'quantity': 10, 'average_price': 100, 'nota': 50, 'tag': 'Ações'},
        {'ticker': 'B.SA', 'quantity': 0, 'average_price': 10, 'nota': 50, 'tag': 'Ações'}
    ]
    prices = {'A.SA': 100, 'B.SA': 10}
    
    results = calculate_smart_buy(assets, prices, invest_brl=500, invest_usd=0)
    for r in results:
        if r['ticker'] == 'A.SA':
            assert r['value_to_buy'] == 0
        elif r['ticker'] == 'B.SA':
            assert r['value_to_buy'] == 500

def test_smart_buy_split():
    assets = [
        {'ticker': 'A.SA', 'quantity': 0, 'nota': 50, 'tag': 'Ações'},
        {'ticker': 'B.SA', 'quantity': 0, 'nota': 50, 'tag': 'Ações'}
    ]
    prices = {'A.SA': 10, 'B.SA': 10}
    
    results = calculate_smart_buy(assets, prices, invest_brl=1000, invest_usd=0)
    for r in results:
        assert r['value_to_buy'] == 500

def test_smart_buy_complex():
    assets = [
        {'ticker': 'A.SA', 'quantity': 2, 'nota': 20, 'tag': 'Ações'},
        {'ticker': 'B.SA', 'quantity': 3, 'nota': 80, 'tag': 'Ações'}
    ]
    prices = {'A.SA': 100, 'B.SA': 100}
    results = calculate_smart_buy(assets, prices, invest_brl=500, invest_usd=0)
    for r in results:
        if r['ticker'] == 'A.SA':
            assert r['value_to_buy'] == 0
        elif r['ticker'] == 'B.SA':
            assert r['value_to_buy'] == 500

def test_smart_buy_limited_cash():
    assets = [
        {'ticker': 'A.SA', 'quantity': 0, 'nota': 50, 'tag': 'Ações'},
        {'ticker': 'B.SA', 'quantity': 5, 'nota': 50, 'tag': 'Ações'}
    ]
    prices = {'A.SA': 100, 'B.SA': 100}
    results = calculate_smart_buy(assets, prices, invest_brl=100, invest_usd=0)
    for r in results:
        if r['ticker'] == 'A.SA':
            assert r['value_to_buy'] == 100
        elif r['ticker'] == 'B.SA':
            assert r['value_to_buy'] == 0

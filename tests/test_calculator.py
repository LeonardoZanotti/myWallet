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

def test_smart_buy_zero_investment():
    assets = [{'ticker': 'A.SA', 'quantity': 10, 'average_price': 10, 'nota': 50, 'tag': 'Ações'}]
    prices = {'A.SA': 10}
    results = calculate_smart_buy(assets, prices, invest_brl=0, invest_usd=0)
    assert results[0]['value_to_buy'] == 0
    assert results[0]['shares_to_buy'] == 0
    assert results[0]['ideal_percent'] == 0

def test_smart_buy_zero_nota():
    assets = [{'ticker': 'A.SA', 'quantity': 10, 'average_price': 10, 'nota': 0, 'tag': 'Ações'}]
    prices = {'A.SA': 10}
    results = calculate_smart_buy(assets, prices, invest_brl=100, invest_usd=0)
    assert results[0]['value_to_buy'] == 0
    assert results[0]['shares_to_buy'] == 0
    assert results[0]['ideal_percent'] == 0

def test_smart_buy_missing_prices():
    assets = [{'ticker': 'A.SA', 'quantity': 10, 'average_price': 20, 'nota': 50, 'tag': 'Ações'}]
    prices = {} # Missing price
    results = calculate_smart_buy(assets, prices, invest_brl=100, invest_usd=0)
    assert results[0]['current_price'] == 20 # Should fallback to average_price

def test_smart_buy_usd_assets():
    assets = [{'ticker': 'VOO', 'quantity': 10, 'average_price': 100, 'nota': 100, 'tag': 'US ETFs'}]
    prices = {'VOO': 100}
    results = calculate_smart_buy(assets, prices, invest_brl=0, invest_usd=100)
    assert len(results) == 1
    assert results[0]['value_to_buy'] == 100

def test_smart_buy_empty_assets():
    results = calculate_smart_buy([], {}, invest_brl=100, invest_usd=100)
    assert results == []

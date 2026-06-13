import pytest
from unittest.mock import patch
from backend.proventos import calculate_proventos

@patch('backend.proventos.get_historical_dividends')
def test_calculate_proventos_basic(mock_get_divs):
    mock_get_divs.return_value = {
        'A.SA': {
            '2026-05-15': 1.5
        }
    }
    
    wallet = {
        'assets': [{'ticker': 'A.SA', 'tag': 'FII', 'currency': 'BRL'}],
        'transactions': [
            {'ticker': 'A.SA', 'date': '2026-05-10', 'type': 'BUY', 'quantity': 10},
            {'ticker': 'A.SA', 'date': '2026-05-20', 'type': 'SELL', 'quantity': 5}
        ]
    }
    
    res = calculate_proventos(wallet)
    
    assert res['total_brl'] == 15.0
    assert len(res['events']) == 1
    assert res['events'][0]['amount'] == 15.0
    assert res['events'][0]['quantity'] == 10.0

@patch('backend.proventos.get_historical_dividends')
def test_calculate_proventos_sell_before_div(mock_get_divs):
    mock_get_divs.return_value = {
        'A.SA': {
            '2026-05-15': 1.5
        }
    }
    
    wallet = {
        'assets': [{'ticker': 'A.SA', 'tag': 'FII', 'currency': 'BRL'}],
        'transactions': [
            {'ticker': 'A.SA', 'date': '2026-05-10', 'type': 'BUY', 'quantity': 10},
            {'ticker': 'A.SA', 'date': '2026-05-14', 'type': 'SELL', 'quantity': 15} # test negative qty fix
        ]
    }
    
    res = calculate_proventos(wallet)
    assert res['total_brl'] == 0.0
    assert len(res['events']) == 0

@patch('backend.proventos.get_historical_dividends')
def test_calculate_proventos_usd(mock_get_divs):
    mock_get_divs.return_value = {
        'US_ETF': {
            '2026-05-15': 2.0
        }
    }
    
    wallet = {
        'assets': [{'ticker': 'US_ETF', 'tag': 'US ETFs', 'currency': 'USD'}],
        'transactions': [
            {'ticker': 'US_ETF', 'date': '2026-05-10', 'type': 'BUY', 'quantity': 5}
        ]
    }
    
    res = calculate_proventos(wallet)
    assert res['total_usd'] == 10.0

@patch('backend.proventos.get_historical_dividends')
def test_calculate_proventos_multiple_divs(mock_get_divs):
    mock_get_divs.return_value = {
        'A.SA': {
            '2026-05-15': 1.0,
            '2026-06-15': 2.0
        }
    }
    
    wallet = {
        'assets': [{'ticker': 'A.SA', 'tag': 'FII', 'currency': 'BRL'}],
        'transactions': [
            {'ticker': 'A.SA', 'date': '2026-05-10', 'type': 'BUY', 'quantity': 10},
            {'ticker': 'A.SA', 'date': '2026-06-10', 'type': 'SELL', 'quantity': 5}
        ]
    }
    
    res = calculate_proventos(wallet)
    assert res['total_brl'] == 20.0
    assert len(res['events']) == 2

@patch('backend.proventos.get_historical_dividends')
def test_calculate_proventos_missing_ticker_in_tx(mock_get_divs):
    mock_get_divs.return_value = {}
    
    wallet = {
        'assets': [],
        'transactions': [
            {'date': '2026-05-10', 'type': 'BUY', 'quantity': 10} # no ticker
        ]
    }
    
    res = calculate_proventos(wallet)
    assert len(res['events']) == 0

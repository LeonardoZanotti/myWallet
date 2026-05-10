import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.validation import (
    ValidationError,
    validate_asset_payload,
    validate_group_payload,
    validate_investment_payload,
    validate_transaction_payload
)


def test_validate_asset_payload_success():
    payload = validate_asset_payload({
        'ticker': 'voo',
        'weight': '40',
        'tag': 'US ETFs',
        'manual_price': ''
    })
    assert payload == {
        'ticker': 'VOO',
        'weight': 40,
        'tag': 'US ETFs',
        'manual_price': None
    }


@pytest.mark.parametrize('payload,error_message', [
    (None, 'Invalid JSON payload.'),
    ({}, 'Missing required fields: ticker, weight, tag.'),
    ({'ticker': '', 'weight': 10, 'tag': 'Ações'}, 'Ticker is required.'),
    ({'ticker': 'A', 'weight': 101, 'tag': 'Ações'}, 'Weight must be between 0 and 100.'),
    ({'ticker': 'A', 'weight': 10, 'tag': ''}, 'Category is required.'),
    ({'ticker': 'A', 'weight': 10, 'tag': 'Ações', 'manual_price': -1}, 'Manual price must be zero or greater.'),
])
def test_validate_asset_payload_errors(payload, error_message):
    with pytest.raises(ValidationError, match=error_message):
        validate_asset_payload(payload)


def test_validate_asset_payload_partial_update():
    payload = validate_asset_payload({'manual_price': '25.5'}, partial=True)
    assert payload == {'manual_price': 25.5}

    with pytest.raises(ValidationError, match='Ticker is required.'):
        validate_asset_payload({'ticker': '   '}, partial=True)


def test_validate_group_payload():
    assert validate_group_payload({'target_percent': ''}) == {'target_percent': None}
    assert validate_group_payload({'target_percent': 30}) == {'target_percent': 30.0}

    with pytest.raises(ValidationError, match='target_percent is required.'):
        validate_group_payload({})
    with pytest.raises(ValidationError, match='Group target must be zero or greater.'):
        validate_group_payload({'target_percent': -10})


def test_validate_investment_payload():
    assert validate_investment_payload({'invest_brl': '100', 'invest_usd': '10'}) == {'invest_brl': 100.0, 'invest_usd': 10.0}

    with pytest.raises(ValidationError, match='Investment amounts must be zero or greater.'):
        validate_investment_payload({'invest_brl': -1, 'invest_usd': 0})
    with pytest.raises(ValidationError, match='invest_brl must be a number.'):
        validate_investment_payload({'invest_brl': 'nope', 'invest_usd': 0})

def test_validate_transaction_payload_success():
    payload = validate_transaction_payload({
        'ticker': ' voo ',
        'date': '2026-05-10',
        'type': 'buy',
        'quantity': '1.5',
        'price': '100.5'
    })
    assert payload == {
        'ticker': 'VOO',
        'date': '2026-05-10',
        'type': 'BUY',
        'quantity': 1.5,
        'price': 100.5,
        'amount': 150.75
    }

def test_validate_transaction_payload_derives_quantity_from_amount():
    payload = validate_transaction_payload({
        'ticker': ' voo ',
        'date': '2026-05-10',
        'type': 'buy',
        'amount': '250',
        'price': '100',
        'currency': 'usd',
        'tag': 'US ETFs',
        'weight': '30'
    })
    assert payload == {
        'ticker': 'VOO',
        'date': '2026-05-10',
        'type': 'BUY',
        'quantity': 2.5,
        'price': 100.0,
        'amount': 250.0,
        'currency': 'USD',
        'tag': 'US ETFs',
        'weight': 30
    }

@pytest.mark.parametrize('payload,error_message', [
    (None, 'Invalid JSON payload.'),
    ({}, 'Missing required fields: ticker, date, type, price.'),
    ({'ticker': '', 'date': '2026-01-01', 'type': 'BUY', 'quantity': 1, 'price': 1}, 'Ticker is required.'),
    ({'ticker': 'A', 'date': 'invalid', 'type': 'BUY', 'quantity': 1, 'price': 1}, 'Date must be in YYYY-MM-DD format.'),
    ({'ticker': 'A', 'date': '2026-01-01', 'type': 'INVALID', 'quantity': 1, 'price': 1}, 'Type must be BUY or SELL.'),
    ({'ticker': 'A', 'date': '2026-01-01', 'type': 'BUY', 'quantity': 0, 'price': 1}, 'Quantity must be greater than zero.'),
    ({'ticker': 'A', 'date': '2026-01-01', 'type': 'BUY', 'quantity': 1, 'price': -1}, 'Price must be zero or greater.'),
    ({'ticker': 'A', 'date': '2026-01-01', 'type': 'BUY', 'price': 1}, 'Either quantity or amount is required.'),
    ({'ticker': 'A', 'date': '2026-01-01', 'type': 'BUY', 'amount': 0, 'price': 1}, 'Amount must be greater than zero.'),
    ({'ticker': 'A', 'date': '2026-01-01', 'type': 'BUY', 'amount': 10, 'price': 0}, 'Price must be greater than zero when amount is used.'),
    ({'ticker': 'A', 'date': '2026-01-01', 'type': 'BUY', 'amount': 10, 'price': 1, 'currency': 'EUR'}, 'Currency must be BRL or USD.'),
    ({'ticker': 'A', 'date': '2026-01-01', 'type': 'BUY', 'amount': 10, 'price': 1, 'tag': '   '}, 'Category is required.'),
    ({'ticker': 'A', 'date': '2026-01-01', 'type': 'BUY', 'amount': 10, 'price': 1, 'weight': 101}, 'Weight must be between 0 and 100.')
])
def test_validate_transaction_payload_errors(payload, error_message):
    with pytest.raises(ValidationError, match=error_message):
        validate_transaction_payload(payload)

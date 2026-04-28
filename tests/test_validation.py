import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.validation import (
    ValidationError,
    validate_asset_payload,
    validate_csv_import_payload,
    validate_group_payload,
    validate_investment_payload,
)


def test_validate_asset_payload_success():
    payload = validate_asset_payload({
        'ticker': 'voo',
        'quantity': '1.5',
        'average_price': '100',
        'nota': '40',
        'tag': 'US ETFs',
        'manual_price': ''
    })
    assert payload == {
        'ticker': 'VOO',
        'quantity': 1.5,
        'average_price': 100.0,
        'nota': 40,
        'tag': 'US ETFs',
        'manual_price': None
    }


@pytest.mark.parametrize('payload,error_message', [
    (None, 'Invalid JSON payload.'),
    ({'ticker': ''}, 'Missing required fields: quantity, average_price, nota, tag.'),
    ({'ticker': 'A', 'quantity': -1, 'average_price': 1, 'nota': 10, 'tag': 'Ações'}, 'Quantity must be zero or greater.'),
    ({'ticker': 'A', 'quantity': 1, 'average_price': -1, 'nota': 10, 'tag': 'Ações'}, 'Average price must be zero or greater.'),
    ({'ticker': 'A', 'quantity': 1, 'average_price': 1, 'nota': 101, 'tag': 'Ações'}, 'Nota must be between 0 and 100.'),
    ({'ticker': 'A', 'quantity': 1, 'average_price': 1, 'nota': 10, 'tag': ''}, 'Category is required.'),
    ({'ticker': 'A', 'quantity': 1, 'average_price': 1, 'nota': 10, 'tag': 'Ações', 'manual_price': -1}, 'Manual price must be zero or greater.'),
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


def test_validate_csv_import_payload():
    assert validate_csv_import_payload({'csv_text': 'ticker\nVOO', 'replace_existing': 1}) == {
        'csv_text': 'ticker\nVOO',
        'replace_existing': True
    }

    with pytest.raises(ValidationError, match='csv_text is required.'):
        validate_csv_import_payload({'csv_text': '   '})

import sys
import os
import json
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import backend.wallet as wallet

@pytest.fixture
def mock_wallet_file(tmp_path):
    wallet_file = tmp_path / "wallet.json"
    with patch('backend.wallet.WALLET_FILE', str(wallet_file)):
        yield str(wallet_file)

def test_load_wallet_missing(mock_wallet_file):
    assert wallet.load_wallet() == {"assets": []}

def test_load_wallet_invalid_json(mock_wallet_file):
    with open(mock_wallet_file, 'w') as f:
        f.write("invalid json")
    assert wallet.load_wallet() == {"assets": []}

def test_save_and_load_wallet(mock_wallet_file):
    data = {"assets": [{"ticker": "A.SA", "quantity": 10}]}
    wallet.save_wallet(data)
    loaded = wallet.load_wallet()
    assert loaded == data

def test_add_asset_new(mock_wallet_file):
    asset_data = {'ticker': 'A.SA', 'quantity': 10, 'average_price': 100, 'nota': 50, 'tag': 'Ações'}
    result = wallet.add_asset(asset_data)
    assert result == asset_data
    
    loaded = wallet.load_wallet()
    assert len(loaded['assets']) == 1
    assert loaded['assets'][0]['ticker'] == 'A.SA'

def test_add_asset_existing(mock_wallet_file):
    # Add first time
    asset_data1 = {'ticker': 'A.SA', 'quantity': 10, 'average_price': 100, 'nota': 50, 'tag': 'Ações'}
    wallet.add_asset(asset_data1)
    
    # Add second time
    asset_data2 = {'ticker': 'A.SA', 'quantity': 10, 'average_price': 50, 'nota': 80, 'tag': 'New Tag'}
    result = wallet.add_asset(asset_data2)
    
    assert result['quantity'] == 20
    assert result['average_price'] == 75.0
    assert result['nota'] == 80
    assert result['tag'] == 'New Tag'
    
    loaded = wallet.load_wallet()
    assert len(loaded['assets']) == 1
    assert loaded['assets'][0]['quantity'] == 20

def test_update_asset(mock_wallet_file):
    asset_data = {'ticker': 'A.SA', 'quantity': 10, 'average_price': 100, 'nota': 50, 'tag': 'Ações'}
    wallet.add_asset(asset_data)
    
    result = wallet.update_asset('A.SA', {'nota': 100, 'quantity': 5})
    assert result['nota'] == 100
    assert result['quantity'] == 5
    
    # Update non-existent
    result_none = wallet.update_asset('B.SA', {'nota': 100})
    assert result_none is None

def test_remove_asset(mock_wallet_file):
    asset_data = {'ticker': 'A.SA', 'quantity': 10, 'average_price': 100, 'nota': 50, 'tag': 'Ações'}
    wallet.add_asset(asset_data)
    
    wallet.remove_asset('A.SA')
    loaded = wallet.load_wallet()
    assert len(loaded['assets']) == 0

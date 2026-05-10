import sys
import os
import json
import pytest
from unittest.mock import patch
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import backend.wallet as wallet

@pytest.fixture
def mock_wallet_file(tmp_path):
    wallet_file = tmp_path / "wallet.json"
    with patch('backend.wallet.WALLET_FILE', str(wallet_file)):
        yield str(wallet_file)

def test_load_wallet_missing(mock_wallet_file):
    assert wallet.load_wallet() == {"assets": [], "groups": {}, "transactions": []}

def test_load_wallet_invalid_json(mock_wallet_file):
    with open(mock_wallet_file, 'w') as f:
        f.write("invalid json")
    assert wallet.load_wallet() == {"assets": [], "groups": {}, "transactions": []}

def test_load_wallet_auto_migration(mock_wallet_file):
    # Missing transactions array, but has assets with qty
    with open(mock_wallet_file, 'w') as f:
        json.dump({"assets": [{"ticker": "A.SA", "quantity": 10, "average_price": 100}], "groups": {}}, f)
        
    data = wallet.load_wallet()
    assert "transactions" in data
    assert len(data["transactions"]) == 1
    tx = data["transactions"][0]
    assert tx["ticker"] == "A.SA"
    assert tx["quantity"] == 10
    assert tx["price"] == 100
    assert tx["type"] == "BUY"
    assert tx["date"] == datetime.date.today().strftime('%Y-%m-%d')

def test_add_asset_new(mock_wallet_file):
    asset_data = {'ticker': 'A.SA', 'weight': 50, 'tag': 'Ações'}
    result = wallet.add_asset(asset_data)
    assert result['quantity'] == 0.0
    assert result['average_price'] == 0.0
    
    loaded = wallet.load_wallet()
    assert len(loaded['assets']) == 1

def test_add_asset_existing(mock_wallet_file):
    wallet.add_asset({'ticker': 'A.SA', 'weight': 50, 'tag': 'Ações'})
    result = wallet.add_asset({'ticker': 'A.SA', 'weight': 80, 'tag': 'New Tag'})
    assert result['weight'] == 80
    assert result['tag'] == 'New Tag'
    
    loaded = wallet.load_wallet()
    assert len(loaded['assets']) == 1

def test_transactions_calculation(mock_wallet_file):
    # Buy 10 @ 100 -> Qty: 10, Avg: 100
    wallet.add_transaction({'ticker': 'A.SA', 'date': '2026-01-01', 'type': 'BUY', 'quantity': 10, 'price': 100})
    loaded = wallet.load_wallet()
    assert loaded['assets'][0]['quantity'] == 10
    assert loaded['assets'][0]['average_price'] == 100

    # Buy 10 @ 50 -> Qty: 20, Avg: 75
    wallet.add_transaction({'ticker': 'A.SA', 'date': '2026-01-02', 'type': 'BUY', 'quantity': 10, 'price': 50})
    loaded = wallet.load_wallet()
    assert loaded['assets'][0]['quantity'] == 20
    assert loaded['assets'][0]['average_price'] == 75

    # Sell 5 @ 100 -> Qty: 15, Avg: 75 (Avg remains the same on sell)
    wallet.add_transaction({'ticker': 'A.SA', 'date': '2026-01-03', 'type': 'SELL', 'quantity': 5, 'price': 100})
    loaded = wallet.load_wallet()
    assert loaded['assets'][0]['quantity'] == 15
    assert loaded['assets'][0]['average_price'] == 75

def test_remove_transaction(mock_wallet_file):
    tx1 = wallet.add_transaction({'ticker': 'A.SA', 'date': '2026-01-01', 'type': 'BUY', 'quantity': 10, 'price': 100})
    tx2 = wallet.add_transaction({'ticker': 'A.SA', 'date': '2026-01-02', 'type': 'BUY', 'quantity': 10, 'price': 50})
    
    loaded = wallet.load_wallet()
    assert loaded['assets'][0]['quantity'] == 20
    assert loaded['assets'][0]['average_price'] == 75

    wallet.remove_transaction(tx1['id'])
    
    loaded = wallet.load_wallet()
    # Now only tx2 remains (10 @ 50)
    assert loaded['assets'][0]['quantity'] == 10
    assert loaded['assets'][0]['average_price'] == 50

def test_update_asset(mock_wallet_file):
    wallet.add_asset({'ticker': 'A.SA', 'weight': 50, 'tag': 'Ações'})
    result = wallet.update_asset('A.SA', {'weight': 100})
    assert result['weight'] == 100
    
    result_none = wallet.update_asset('B.SA', {'weight': 100})
    assert result_none is None

def test_remove_asset(mock_wallet_file):
    wallet.add_transaction({'ticker': 'A.SA', 'date': '2026-01-01', 'type': 'BUY', 'quantity': 10, 'price': 100})
    assert len(wallet.load_wallet()['transactions']) == 1
    
    wallet.remove_asset('A.SA')
    loaded = wallet.load_wallet()
    assert len(loaded['assets']) == 0
    assert len(loaded['transactions']) == 0

    assert wallet.remove_asset('B.SA') == False

def test_update_group(mock_wallet_file):
    wallet.save_wallet({"assets": [], "groups": {}, "transactions": []})
    updated = wallet.update_group("Ações", {"target_percent": 30})
    assert updated["target_percent"] == 30
    
    loaded = wallet.load_wallet()
    assert loaded["groups"]["Ações"]["target_percent"] == 30

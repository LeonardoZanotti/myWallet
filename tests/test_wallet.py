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

def test_load_wallet_migration_skips_zero_quantity_assets(mock_wallet_file):
    with open(mock_wallet_file, 'w') as f:
        json.dump({"assets": [{"ticker": "A.SA", "quantity": 0, "average_price": 100}]}, f)

    data = wallet.load_wallet()

    assert data["groups"] == {}
    assert data["transactions"] == []
    assert data["assets"] == [{"ticker": "A.SA", "quantity": 0.0, "average_price": 0.0, "weight": 0, "tag": "Ações"}]

def test_load_wallet_normalizes_transaction_defaults_and_creates_asset(mock_wallet_file):
    with open(mock_wallet_file, 'w') as f:
        json.dump({
            "assets": [],
            "groups": {},
            "transactions": [
                {"ticker": "voo", "type": "buy", "amount": 250, "price": 100, "currency": "usd", "tag": "US ETFs", "weight": 40},
                {"ticker": "ABC", "type": "BUY", "quantity": 1, "price": 10, "tag": "Stocks"}
            ]
        }, f)

    data = wallet.load_wallet()
    voo = next(asset for asset in data["assets"] if asset["ticker"] == "VOO")
    abc = next(asset for asset in data["assets"] if asset["ticker"] == "ABC")
    tx_by_ticker = {tx["ticker"]: tx for tx in data["transactions"]}

    assert voo == {"ticker": "VOO", "weight": 40, "tag": "US ETFs", "quantity": 2.5, "average_price": 100.0}
    assert abc["tag"] == "Stocks"
    assert abc["quantity"] == 1.0
    assert tx_by_ticker["VOO"]["date"] == datetime.date.today().strftime('%Y-%m-%d')
    assert tx_by_ticker["VOO"]["quantity"] == 2.5
    assert tx_by_ticker["VOO"]["currency"] == "USD"
    assert tx_by_ticker["ABC"]["currency"] == "USD"

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

def test_add_asset_existing_after_non_matching_asset(mock_wallet_file):
    wallet.add_asset({'ticker': 'A.SA', 'weight': 50, 'tag': 'Ações'})
    wallet.add_asset({'ticker': 'B.SA', 'weight': 20, 'tag': 'Ações'})

    result = wallet.add_asset({'ticker': 'B.SA', 'weight': 80, 'tag': 'BR ETFs'})

    assert result['ticker'] == 'B.SA'
    assert result['weight'] == 80
    assert result['tag'] == 'BR ETFs'
    assert len(wallet.load_wallet()['assets']) == 2

def test_transactions_calculation(mock_wallet_file):
    wallet.add_transaction({'ticker': 'A.SA', 'date': '2026-01-01', 'type': 'BUY', 'quantity': 10, 'price': 100})
    loaded = wallet.load_wallet()
    assert loaded['assets'][0]['quantity'] == 10
    assert loaded['assets'][0]['average_price'] == 100

    wallet.add_transaction({'ticker': 'A.SA', 'date': '2026-01-02', 'type': 'BUY', 'quantity': 10, 'price': 50})
    loaded = wallet.load_wallet()
    assert loaded['assets'][0]['quantity'] == 20
    assert loaded['assets'][0]['average_price'] == 75

    wallet.add_transaction({'ticker': 'A.SA', 'date': '2026-01-03', 'type': 'SELL', 'quantity': 5, 'price': 100})
    loaded = wallet.load_wallet()
    assert loaded['assets'][0]['quantity'] == 15
    assert loaded['assets'][0]['average_price'] == 75

@patch('backend.finance.get_historical_exchange_rate', return_value=5.0)
def test_amount_transaction_creates_usd_asset_and_summary(mock_fx, mock_wallet_file):
    wallet.add_transaction({
        'ticker': 'VOO',
        'date': '2026-05-01',
        'type': 'BUY',
        'amount': 250,
        'price': 100,
        'currency': 'USD',
        'tag': 'US ETFs',
        'weight': 40
    })

    loaded = wallet.load_wallet()
    asset = loaded['assets'][0]
    tx = loaded['transactions'][0]
    summary = wallet.build_investment_summary(loaded, exchange_rate=5.0)

    assert asset['ticker'] == 'VOO'
    assert asset['tag'] == 'US ETFs'
    assert asset['weight'] == 40
    assert asset['quantity'] == 2.5
    assert asset['average_price'] == 100
    assert tx['currency'] == 'USD'
    assert tx['amount'] == 250
    assert summary['total_buy_usd'] == 250
    assert summary['gross_invested_brl_equivalent'] == 1250
    assert summary['monthly'][0]['month'] == '2026-05'

def test_sell_edge_cases_and_investment_summary(mock_wallet_file):
    wallet.save_wallet({
        "assets": [
            {"ticker": "A.SA", "weight": 10, "tag": "Ações", "quantity": 0, "average_price": 0},
            {"ticker": "B.SA", "weight": 10, "tag": "Ações", "quantity": 0, "average_price": 0},
            {"ticker": "VOO", "weight": 10, "tag": "US ETFs", "quantity": 0, "average_price": 0}
        ],
        "groups": {},
        "transactions": [
            {"id": "1", "ticker": "A.SA", "date": "2026-01-01", "type": "SELL", "quantity": 1, "price": 100, "amount": 100, "currency": "BRL"},
            {"id": "2", "ticker": "B.SA", "date": "2026-01-01", "type": "BUY", "quantity": 1, "price": 50, "amount": 50, "currency": "BRL"},
            {"id": "3", "ticker": "B.SA", "date": "2026-01-02", "type": "SELL", "quantity": 2, "price": 60, "amount": 120, "currency": "BRL"},
            {"id": "4", "ticker": "VOO", "date": "2026-01-01", "type": "BUY", "quantity": 1, "price": 10, "amount": 10, "currency": "USD"},
            {"id": "5", "ticker": "VOO", "date": "2026-01-02", "type": "SELL", "quantity": 0.25, "price": 12, "amount": 3, "currency": "USD"},
            {"id": "6", "ticker": "NODATE", "type": "SELL", "quantity": 1, "price": 7, "amount": 7, "currency": "BRL"}
        ]
    })

    loaded = wallet.load_wallet()
    summary = wallet.build_investment_summary(loaded, exchange_rate=5.0)

    assert [asset["ticker"] for asset in loaded["assets"]] == ["VOO"]
    assert loaded["assets"][0]["quantity"] == 0.75
    assert loaded["assets"][0]["average_price"] == 10
    assert summary["total_buy_brl"] == 50
    assert summary["total_sell_brl"] == 227
    assert summary["total_buy_usd"] == 10
    assert summary["total_sell_usd"] == 3
    assert summary["gross_invested_brl_equivalent"] == 100
    assert summary["net_invested_brl_equivalent"] == -142
    assert sum(month["sell_brl"] for month in summary["monthly"]) == 227
    voo_summary = next(item for item in summary["by_asset"] if item["ticker"] == "VOO")
    assert voo_summary["sell_amount"] == 3
    assert voo_summary["quantity"] == 0.75

def test_recalculate_asset_state_returns_none_for_unknown_asset(mock_wallet_file):
    data = {"assets": [], "groups": {}, "transactions": []}
    assert wallet.recalculate_asset_state("MISSING", data) is None

def test_recalculate_asset_state_ignores_unknown_transaction_type(mock_wallet_file):
    data = {
        "assets": [{"ticker": "A.SA", "weight": 10, "tag": "Ações"}],
        "groups": {},
        "transactions": [
            {"ticker": "A.SA", "date": "2026-01-01", "type": "DIVIDEND", "quantity": 1, "price": 10}
        ]
    }

    asset = wallet.recalculate_asset_state("A.SA", data)

    assert asset["quantity"] == 0.0
    assert asset["average_price"] == 0.0

def test_investment_summary_keeps_undated_asset_totals_out_of_months():
    summary = wallet.build_investment_summary({
        "assets": [],
        "transactions": [
            {"ticker": "A.SA", "type": "BUY", "quantity": 1, "price": 10, "amount": 10, "currency": "BRL", "date": ""}
        ]
    })

    assert summary["total_buy_brl"] == 10
    assert summary["monthly"] == []
    assert summary["by_asset"][0]["buy_amount"] == 10

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

    assert wallet.remove_transaction('missing-id') is False

def test_sold_out_asset_is_pruned_from_current_holdings(mock_wallet_file):
    wallet.add_transaction({'ticker': 'A.SA', 'date': '2026-01-01', 'type': 'BUY', 'quantity': 10, 'price': 100})
    wallet.add_transaction({'ticker': 'A.SA', 'date': '2026-01-02', 'type': 'SELL', 'quantity': 10, 'price': 110})

    loaded = wallet.load_wallet()

    assert loaded['assets'] == []
    assert len(loaded['transactions']) == 2

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

    updated = wallet.update_group("Ações", {"target_percent": 40})
    assert updated["target_percent"] == 40
    
    loaded = wallet.load_wallet()
    assert loaded["groups"]["Ações"]["target_percent"] == 40

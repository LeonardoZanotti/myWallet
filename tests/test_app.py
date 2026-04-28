import sys
import os
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from backend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index(client):
    with patch('backend.app.Flask.send_static_file') as mock_send:
        mock_send.return_value = "index.html content"
        response = client.get('/')
        assert response.status_code == 200
        mock_send.assert_called_with('index.html')

@patch('backend.app.load_wallet')
@patch('backend.app.get_current_prices')
@patch('backend.app.get_exchange_rate')
def test_get_wallet(mock_exchange, mock_prices, mock_load, client):
    mock_load.return_value = {
        "assets": [
            {'ticker': 'A.SA', 'quantity': 10, 'average_price': 10, 'tag': 'Ações'},
            {'ticker': 'VOO', 'quantity': 5, 'average_price': 100, 'tag': 'US ETFs'},
            {'ticker': 'B.SA', 'quantity': 5, 'average_price': 10, 'tag': 'Ações'} # no price found
        ]
    }
    mock_prices.return_value = {'A.SA': 20, 'VOO': 110, 'B.SA': None}
    mock_exchange.return_value = 5.0
    
    response = client.get('/api/wallet')
    assert response.status_code == 200
    data = response.get_json()
    assert data['exchange_rate'] == 5.0
    assert len(data['assets']) == 3
    
    assert data['assets'][0]['currency'] == 'BRL'
    assert data['assets'][0]['current_price'] == 20
    assert data['assets'][0]['variation'] == 100.0 # (20-10)/10 * 100
    assert data['assets'][0]['total_value'] == 200
    
    assert data['assets'][1]['currency'] == 'USD'
    assert data['assets'][1]['current_price'] == 110
    assert data['assets'][1]['variation'] == 10.0
    
    # Missing price test
    assert data['assets'][2]['current_price'] is None
    assert data['assets'][2]['variation'] == 0
    assert data['assets'][2]['total_value'] == 50

@patch('backend.app.load_wallet')
@patch('backend.app.get_current_prices')
@patch('backend.app.get_exchange_rate')
def test_get_wallet_zero_avg_price(mock_exchange, mock_prices, mock_load, client):
    mock_load.return_value = {
        "assets": [
            {'ticker': 'A.SA', 'quantity': 10, 'average_price': 0, 'tag': 'Ações'}
        ]
    }
    mock_prices.return_value = {'A.SA': 20}
    mock_exchange.return_value = 5.0
    
    response = client.get('/api/wallet')
    data = response.get_json()
    assert data['assets'][0]['variation'] == 0

@patch('backend.app.add_asset')
def test_create_asset(mock_add, client):
    mock_add.return_value = {'ticker': 'A.SA'}
    response = client.post('/api/wallet/asset', json={
        'ticker': 'A.SA',
        'quantity': 1,
        'average_price': 10,
        'nota': 50,
        'tag': 'Ações'
    })
    assert response.status_code == 200
    assert response.get_json() == {'ticker': 'A.SA'}

@patch('backend.app.add_asset')
def test_create_asset_validation_error(mock_add, client):
    response = client.post('/api/wallet/asset', json={'ticker': '', 'quantity': -1})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Missing required fields: average_price, nota, tag.'
    mock_add.assert_not_called()

@patch('backend.app.update_asset')
def test_edit_asset(mock_update, client):
    mock_update.return_value = {'ticker': 'A.SA', 'nota': 100}
    response = client.put('/api/wallet/asset/A.SA', json={'nota': 100})
    assert response.status_code == 200
    assert response.get_json() == {'ticker': 'A.SA', 'nota': 100}

@patch('backend.app.update_asset')
def test_edit_asset_validation_error(mock_update, client):
    response = client.put('/api/wallet/asset/A.SA', json={'nota': 'bad'})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'nota must be an integer.'
    mock_update.assert_not_called()

@patch('backend.app.update_asset')
def test_edit_asset_not_found(mock_update, client):
    mock_update.return_value = None
    response = client.put('/api/wallet/asset/A.SA', json={'nota': 100})
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Asset not found.'

@patch('backend.app.remove_asset')
def test_delete_asset(mock_remove, client):
    mock_remove.return_value = True
    response = client.delete('/api/wallet/asset/A.SA')
    assert response.status_code == 200
    assert response.get_json() == {"status": "success"}

@patch('backend.app.remove_asset')
def test_delete_asset_not_found(mock_remove, client):
    mock_remove.return_value = False
    response = client.delete('/api/wallet/asset/A.SA')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Asset not found.'

@patch('backend.app.update_group')
def test_edit_group(mock_update, client):
    mock_update.return_value = {'target_percent': 30}
    response = client.put('/api/wallet/group/Ações', json={'target_percent': 30})
    assert response.status_code == 200
    assert response.get_json() == {'target_percent': 30}

@patch('backend.app.update_group')
def test_edit_group_validation_error(mock_update, client):
    response = client.put('/api/wallet/group/Ações', json={'target_percent': -1})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Group target must be zero or greater.'
    mock_update.assert_not_called()

@patch('backend.app.load_wallet')
@patch('backend.app.get_current_prices')
@patch('backend.app.get_exchange_rate')
@patch('backend.app.calculate_smart_buy')
def test_smart_buy(mock_calc, mock_exchange, mock_prices, mock_load, client):
    mock_load.return_value = {
        "assets": [
            {'ticker': 'A.SA', 'tag': 'Ações'},
            {'ticker': 'VOO', 'tag': 'US ETFs'}
        ]
    }
    mock_prices.return_value = {'A.SA': 20, 'VOO': 110}
    mock_exchange.return_value = 5.0
    mock_calc.return_value = ([{'ticker': 'A.SA', 'value_to_buy': 100}], 5, 0)
    
    response = client.post('/api/smart-buy', json={'invest_brl': 100, 'invest_usd': 50})
    assert response.status_code == 200
    assert response.get_json() == {
        "recommendations": [{'ticker': 'A.SA', 'value_to_buy': 100}],
        "leftover_brl": 5,
        "leftover_usd": 0
    }
    
    # Check if currencies were injected
    called_assets = mock_calc.call_args[0][0]
    assert called_assets[0]['currency'] == 'BRL'
    assert called_assets[1]['currency'] == 'USD'

@patch('backend.app.calculate_smart_buy')
def test_smart_buy_validation_error(mock_calc, client):
    response = client.post('/api/smart-buy', json={'invest_brl': -1, 'invest_usd': 0})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Investment amounts must be zero or greater.'
    mock_calc.assert_not_called()

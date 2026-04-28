import json
import os

WALLET_FILE = os.path.join(os.path.dirname(__file__), 'wallet.json')

def load_wallet():
    if not os.path.exists(WALLET_FILE):
        return {"assets": [], "groups": {}}
    with open(WALLET_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if "groups" not in data:
                data["groups"] = {}
            return data
        except json.JSONDecodeError:
            return {"assets": [], "groups": {}}

def save_wallet(data):
    with open(WALLET_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_asset(asset_data):
    """
    asset_data should have:
    - ticker: str (e.g., 'BBOV11.SA')
    - quantity: float
    - average_price: float
    - nota: int (weight)
    - tag: str (e.g., 'Brazil ETF')
    """
    wallet = load_wallet()
    # Check if asset exists, if so update it
    for asset in wallet['assets']:
        if asset['ticker'] == asset_data['ticker']:
            # Weighted average for new price
            total_value = asset['quantity'] * asset['average_price'] + asset_data['quantity'] * asset_data['average_price']
            total_qty = asset['quantity'] + asset_data['quantity']
            asset['average_price'] = total_value / total_qty
            asset['quantity'] = total_qty
            # Update other fields if provided
            if 'nota' in asset_data: asset['nota'] = asset_data['nota']
            if 'tag' in asset_data: asset['tag'] = asset_data['tag']
            save_wallet(wallet)
            return asset
    
    # Otherwise add new
    wallet['assets'].append(asset_data)
    save_wallet(wallet)
    return asset_data

def update_asset(ticker, update_data):
    wallet = load_wallet()
    for asset in wallet['assets']:
        if asset['ticker'] == ticker:
            for key, value in update_data.items():
                asset[key] = value
            save_wallet(wallet)
            return asset
    return None

def remove_asset(ticker):
    wallet = load_wallet()
    initial_count = len(wallet['assets'])
    wallet['assets'] = [a for a in wallet['assets'] if a['ticker'] != ticker]
    if len(wallet['assets']) == initial_count:
        return False
    save_wallet(wallet)
    return True

def update_group(tag, update_data):
    wallet = load_wallet()
    if tag not in wallet['groups']:
        wallet['groups'][tag] = {}
    for key, value in update_data.items():
        wallet['groups'][tag][key] = value
    save_wallet(wallet)
    return wallet['groups'][tag]

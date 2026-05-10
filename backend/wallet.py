import json
import os
import uuid
import datetime

WALLET_FILE = os.path.join(os.path.dirname(__file__), 'wallet.json')

def load_wallet():
    if not os.path.exists(WALLET_FILE):
        return {"assets": [], "groups": {}, "transactions": []}
    with open(WALLET_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            needs_save = False
            if "groups" not in data:
                data["groups"] = {}
                needs_save = True
            if "transactions" not in data:
                data["transactions"] = []
                today = datetime.date.today().strftime('%Y-%m-%d')
                for asset in data.get('assets', []):
                    qty = asset.get('quantity', 0)
                    price = asset.get('average_price', 0)
                    if qty > 0:
                        data['transactions'].append({
                            'id': str(uuid.uuid4()),
                            'date': today,
                            'type': 'BUY',
                            'ticker': asset['ticker'],
                            'quantity': qty,
                            'price': price
                        })
                needs_save = True
                
            for asset in data.get('assets', []):
                asset.setdefault('quantity', 0.0)
                asset.setdefault('average_price', 0.0)
                
            if needs_save:
                save_wallet(data)
            return data
        except json.JSONDecodeError:
            return {"assets": [], "groups": {}, "transactions": []}

def save_wallet(data):
    with open(WALLET_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def recalculate_asset_state(ticker, wallet):
    txs = sorted([tx for tx in wallet.get('transactions', []) if tx['ticker'] == ticker], key=lambda x: x['date'])
    
    qty = 0.0
    total_cost = 0.0
    
    for tx in txs:
        if tx['type'] == 'BUY':
            qty += tx['quantity']
            total_cost += tx['quantity'] * tx['price']
        elif tx['type'] == 'SELL':
            if qty > 0:
                avg_price = total_cost / qty
                qty -= tx['quantity']
                if qty < 0:
                    qty = 0.0
                total_cost = qty * avg_price
            else:
                qty = 0.0
                total_cost = 0.0
                
    avg_price = (total_cost / qty) if qty > 0 else 0.0
    
    for asset in wallet['assets']:
        if asset['ticker'] == ticker:
            asset['quantity'] = qty
            asset['average_price'] = avg_price
            return asset
            
    return None

def add_transaction(tx_data):
    wallet = load_wallet()
    tx_data['id'] = str(uuid.uuid4())
    wallet['transactions'].append(tx_data)
    
    exists = any(a['ticker'] == tx_data['ticker'] for a in wallet['assets'])
    if not exists:
        wallet['assets'].append({
            'ticker': tx_data['ticker'],
            'weight': 0,
            'tag': 'Ações',
            'quantity': 0.0,
            'average_price': 0.0
        })
        
    recalculate_asset_state(tx_data['ticker'], wallet)
    save_wallet(wallet)
    return tx_data

def remove_transaction(tx_id):
    wallet = load_wallet()
    tx_to_remove = next((tx for tx in wallet['transactions'] if tx['id'] == tx_id), None)
    if not tx_to_remove:
        return False
        
    wallet['transactions'] = [tx for tx in wallet['transactions'] if tx['id'] != tx_id]
    recalculate_asset_state(tx_to_remove['ticker'], wallet)
    save_wallet(wallet)
    return True

def add_asset(asset_data):
    wallet = load_wallet()
    for asset in wallet['assets']:
        if asset['ticker'] == asset_data['ticker']:
            if 'weight' in asset_data: asset['weight'] = asset_data['weight']
            if 'tag' in asset_data: asset['tag'] = asset_data['tag']
            save_wallet(wallet)
            return asset
    
    asset_data['quantity'] = 0.0
    asset_data['average_price'] = 0.0
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
    wallet['transactions'] = [tx for tx in wallet['transactions'] if tx['ticker'] != ticker]
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

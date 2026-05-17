import json
import os
import uuid
import datetime

from backend.config import BRL_CATEGORIES

WALLET_FILE = os.path.join(os.path.dirname(__file__), 'wallet.json')
EPSILON = 1e-9

def _empty_wallet():
    return {"assets": [], "groups": {}, "transactions": []}

def _detect_currency(asset):
    tag = asset.get('tag', '')
    ticker = asset.get('ticker', '')
    return 'BRL' if tag in BRL_CATEGORIES or ticker.endswith('.SA') else 'USD'

def _default_tag_for_currency(currency):
    return 'Stocks' if currency == 'USD' else 'Ações'

def _transaction_amount(tx):
    amount = tx.get('amount')
    if amount not in ('', None):
        return float(amount)
    return float(tx.get('quantity', 0) or 0) * float(tx.get('price', 0) or 0)

def _normalize_transaction(tx, assets_by_ticker):
    tx['ticker'] = str(tx.get('ticker', '')).strip().upper()
    tx['type'] = str(tx.get('type', 'BUY')).strip().upper()
    tx['quantity'] = float(tx.get('quantity', 0) or 0)
    tx['price'] = float(tx.get('price', 0) or 0)
    tx['amount'] = _transaction_amount(tx)
    if tx['quantity'] == 0 and tx['amount'] > 0 and tx['price'] > 0:
        tx['quantity'] = tx['amount'] / tx['price']
    tx.setdefault('id', str(uuid.uuid4()))

    if not tx.get('date'):
        tx['date'] = datetime.date.today().strftime('%Y-%m-%d')

    currency = str(tx.get('currency', '')).strip().upper()
    if currency not in ('BRL', 'USD'):
        asset = assets_by_ticker.get(tx['ticker'], {'ticker': tx['ticker'], 'tag': tx.get('tag', '')})
        currency = _detect_currency(asset)
    tx['currency'] = currency

    if 'historical_fx' in tx and tx['historical_fx'] not in ('', None):
        tx['historical_fx'] = float(tx['historical_fx'])
        
    return tx

def _recalculate_all_asset_states(wallet):
    tickers = {asset.get('ticker') for asset in wallet.get('assets', [])}
    tickers.update(tx.get('ticker') for tx in wallet.get('transactions', []))
    for ticker in sorted(t for t in tickers if t):
        recalculate_asset_state(ticker, wallet)

def _prune_sold_assets(wallet):
    tx_tickers = {tx.get('ticker') for tx in wallet.get('transactions', [])}
    wallet['assets'] = [
        asset for asset in wallet.get('assets', [])
        if asset.get('ticker') not in tx_tickers or abs(float(asset.get('quantity', 0) or 0)) > EPSILON
    ]

def load_wallet():
    if not os.path.exists(WALLET_FILE):
        return _empty_wallet()
    with open(WALLET_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            original = json.dumps(data, sort_keys=True)
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
                            'price': price,
                            'amount': qty * price,
                            'currency': _detect_currency(asset)
                        })
                needs_save = True
                
            assets_by_ticker = {}
            for asset in data.get('assets', []):
                asset['ticker'] = str(asset.get('ticker', '')).strip().upper()
                asset.setdefault('quantity', 0.0)
                asset.setdefault('average_price', 0.0)
                asset.setdefault('weight', 0)
                asset.setdefault('tag', _default_tag_for_currency(_detect_currency(asset)))
                assets_by_ticker[asset['ticker']] = asset

            for tx in data.get('transactions', []):
                _normalize_transaction(tx, assets_by_ticker)
                if tx['ticker'] and tx['ticker'] not in assets_by_ticker:
                    tag = tx.get('tag') or _default_tag_for_currency(tx['currency'])
                    asset = {
                        'ticker': tx['ticker'],
                        'weight': int(tx.get('weight', 0) or 0),
                        'tag': tag,
                        'quantity': 0.0,
                        'average_price': 0.0
                    }
                    data['assets'].append(asset)
                    assets_by_ticker[tx['ticker']] = asset

            _recalculate_all_asset_states(data)
            _prune_sold_assets(data)
                
            if needs_save or json.dumps(data, sort_keys=True) != original:
                save_wallet(data)
            return data
        except json.JSONDecodeError:
            return _empty_wallet()

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
            total_cost += _transaction_amount(tx)
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
                
    qty = round(qty, 8)
    avg_price = round((total_cost / qty), 8) if qty > 0 else 0.0
    
    for asset in wallet['assets']:
        if asset['ticker'] == ticker:
            asset['quantity'] = qty
            asset['average_price'] = avg_price
            return asset
            
    return None

def add_transaction(tx_data):
    from backend.finance import get_historical_exchange_rate
    wallet = load_wallet()
    assets_by_ticker = {asset['ticker']: asset for asset in wallet.get('assets', [])}
    _normalize_transaction(tx_data, assets_by_ticker)

    if tx_data['currency'] == 'USD' and ('historical_fx' not in tx_data or not tx_data['historical_fx']):
        tx_data['historical_fx'] = get_historical_exchange_rate(tx_data['date'])

    tx_data['id'] = str(uuid.uuid4())
    wallet['transactions'].append(tx_data)
    
    asset = next((a for a in wallet['assets'] if a['ticker'] == tx_data['ticker']), None)
    if asset:
        if tx_data.get('tag'):
            asset['tag'] = tx_data['tag']
        if 'weight' in tx_data:
            asset['weight'] = tx_data['weight']
    else:
        wallet['assets'].append({
            'ticker': tx_data['ticker'],
            'weight': tx_data.get('weight', 0),
            'tag': tx_data.get('tag') or _default_tag_for_currency(tx_data['currency']),
            'quantity': 0.0,
            'average_price': 0.0
        })
        
    recalculate_asset_state(tx_data['ticker'], wallet)
    _prune_sold_assets(wallet)
    save_wallet(wallet)
    return tx_data

def remove_transaction(tx_id):
    wallet = load_wallet()
    tx_to_remove = next((tx for tx in wallet['transactions'] if tx['id'] == tx_id), None)
    if not tx_to_remove:
        return False
        
    wallet['transactions'] = [tx for tx in wallet['transactions'] if tx['id'] != tx_id]
    recalculate_asset_state(tx_to_remove['ticker'], wallet)
    _prune_sold_assets(wallet)
    save_wallet(wallet)
    return True

def build_investment_summary(wallet, exchange_rate=5.0):
    summary = {
        'total_buy_brl': 0.0,
        'total_buy_usd': 0.0,
        'total_sell_brl': 0.0,
        'total_sell_usd': 0.0,
        'net_invested_brl_equivalent': 0.0,
        'gross_invested_brl_equivalent': 0.0,
        'monthly': [],
        'by_asset': []
    }
    monthly = {}
    by_asset = {}

    assets_by_ticker = {asset['ticker']: asset for asset in wallet.get('assets', [])}

    for tx in wallet.get('transactions', []):
        ticker = tx.get('ticker', '')
        amount = _transaction_amount(tx)
        currency = tx.get('currency') or _detect_currency(assets_by_ticker.get(ticker, {'ticker': ticker}))
        kind = 'buy' if tx.get('type') == 'BUY' else 'sell'
        sign = 1 if kind == 'buy' else -1
        month = str(tx.get('date', ''))[:7]
        native_key = f'{kind}_{currency.lower()}'
        
        tx_fx = tx.get('historical_fx') or exchange_rate
        brl_eq = amount if currency == 'BRL' else amount * tx_fx

        if tx.get('type') == 'BUY':
            summary[f'total_buy_{currency.lower()}'] += amount
            summary['gross_invested_brl_equivalent'] += brl_eq
        else:
            summary[f'total_sell_{currency.lower()}'] += amount

        summary['net_invested_brl_equivalent'] += sign * brl_eq

        if month:
            bucket = monthly.setdefault(month, {
                'month': month,
                'buy_brl': 0.0,
                'buy_usd': 0.0,
                'sell_brl': 0.0,
                'sell_usd': 0.0,
                'net_brl_equivalent': 0.0,
                'gross_brl_equivalent': 0.0
            })
            bucket[native_key] += amount
            bucket['net_brl_equivalent'] += sign * brl_eq
            if tx.get('type') == 'BUY':
                bucket['gross_brl_equivalent'] += brl_eq

        asset_bucket = by_asset.setdefault(ticker, {
            'ticker': ticker,
            'tag': assets_by_ticker.get(ticker, {}).get('tag', tx.get('tag', '')),
            'currency': currency,
            'buy_amount': 0.0,
            'sell_amount': 0.0,
            'net_amount': 0.0,
            'quantity': 0.0
        })
        if tx.get('type') == 'BUY':
            asset_bucket['buy_amount'] += amount
            asset_bucket['quantity'] += tx.get('quantity', 0)
        else:
            asset_bucket['sell_amount'] += amount
            asset_bucket['quantity'] -= tx.get('quantity', 0)
        asset_bucket['net_amount'] = asset_bucket['buy_amount'] - asset_bucket['sell_amount']

    summary['monthly'] = [monthly[key] for key in sorted(monthly)]
    summary['by_asset'] = sorted(by_asset.values(), key=lambda item: item['buy_amount'], reverse=True)
    return summary

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

from backend.finance import get_historical_dividends
from backend.wallet import _detect_currency
import datetime

def calculate_proventos(wallet, exchange_rate=5.0):
    assets = wallet.get('assets', [])
    transactions = wallet.get('transactions', [])
    
    # fetch dividend data
    dividends_data = get_historical_dividends(assets)
    
    tx_by_ticker = {}
    for tx in transactions:
        ticker = tx.get('ticker')
        if not ticker: continue
        if ticker not in tx_by_ticker:
            tx_by_ticker[ticker] = []
        tx_by_ticker[ticker].append((tx['date'], tx['type'], tx.get('quantity', 0)))
        
    for ticker in tx_by_ticker:
        tx_by_ticker[ticker].sort(key=lambda x: x[0])
        
    proventos = []
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    for asset in assets:
        ticker = asset['ticker']
        currency = _detect_currency(asset)
        asset_divs = dividends_data.get(ticker, {})
        asset_txs = tx_by_ticker.get(ticker, [])
        
        div_dates = sorted(asset_divs.keys())
        
        for div_date in div_dates:
            div_amount_per_share = asset_divs[div_date]
            
            qty_held = 0.0
            for tx_date, tx_type, tx_qty in asset_txs:
                if tx_date < div_date: # You must own it BEFORE the ex-dividend date
                    if tx_type == 'BUY':
                        qty_held += tx_qty
                    elif tx_type == 'SELL':
                        qty_held -= tx_qty
                        if qty_held < 0: qty_held = 0.0
            
            if qty_held > 1e-9:
                total_div = qty_held * div_amount_per_share
                # Simple heuristic for payment status: if ex-date was more than 15 days ago, consider it paid
                # since yfinance doesn't provide exact payment dates.
                
                status = 'A Receber'
                ex_date_obj = datetime.datetime.strptime(div_date, '%Y-%m-%d')
                if (datetime.datetime.now() - ex_date_obj).days >= 15:
                    status = 'Pago'
                    
                proventos.append({
                    'ticker': ticker,
                    'tag': asset.get('tag', ''),
                    'currency': currency,
                    'date': div_date,
                    'amount': total_div,
                    'amount_per_share': div_amount_per_share,
                    'quantity': qty_held,
                    'status': status
                })
                
    # Build summary similar to investment_summary
    monthly = {}
    by_asset = {}
    total_all_time_brl = 0.0
    total_all_time_usd = 0.0
    
    for p in proventos:
        ticker = p['ticker']
        currency = p['currency']
        amount = p['amount']
        
        amount = p['amount']
        month = p['date'][:7]
        
        if currency == 'USD':
            total_all_time_usd += amount
        else:
            total_all_time_brl += amount
            
        bucket = monthly.setdefault(month, {
            'month': month,
            'dividend_brl': 0.0,
            'dividend_usd': 0.0
        })
        if currency == 'USD':
            bucket['dividend_usd'] += amount
        else:
            bucket['dividend_brl'] += amount
            
        asset_bucket = by_asset.setdefault(ticker, {
            'ticker': ticker,
            'tag': p['tag'],
            'currency': currency,
            'dividend_amount': 0.0
        })
        asset_bucket['dividend_amount'] += amount

    # Sort events by date descending
    proventos.sort(key=lambda x: x['date'], reverse=True)

    return {
        'events': proventos,
        'monthly': [monthly[m] for m in sorted(monthly.keys())],
        'by_asset': sorted(by_asset.values(), key=lambda x: x['dividend_amount'], reverse=True),
        'total_brl': total_all_time_brl,
        'total_usd': total_all_time_usd
    }

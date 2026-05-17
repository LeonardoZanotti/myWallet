import yfinance as yf

from backend.config import BRL_CATEGORIES

def _format_ticker_for_yahoo(ticker, tag):
    if tag in BRL_CATEGORIES and not ticker.endswith('.SA'):
        return f"{ticker}.SA"
    return ticker

def get_current_prices(assets):
    """
    Fetches the current market price for a list of assets.
    Returns a dictionary: { 'TICKER': price, ... }
    """
    if not assets:
        return {}
        
    prices = {}
    try:
        for asset in assets:
            ticker = asset['ticker']
            tag = asset.get('tag', '')
            
            query_ticker = _format_ticker_for_yahoo(ticker, tag)
                
            ticker_obj = yf.Ticker(query_ticker)
            try:
                hist = ticker_obj.history(period="1d")
                if not hist.empty:
                    prices[ticker] = float(hist['Close'].iloc[-1])
                else:
                    prices[ticker] = None
            except Exception:
                prices[ticker] = None
    except Exception as e:
        print(f"Error fetching prices: {e}")
    return prices

def get_exchange_rate():
    """Fetches the current USD to BRL exchange rate."""
    try:
        ticker = yf.Ticker("USDBRL=X")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
    return 5.0  # Fallback exchange rate

import datetime

def get_historical_exchange_rate(date_str):
    """Fetches the USD to BRL exchange rate for a specific date."""
    try:
        ticker = yf.Ticker("BRL=X")
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        end_obj = date_obj + datetime.timedelta(days=5) # 5 days to hit a weekday
        end_str = end_obj.strftime('%Y-%m-%d')
        hist = ticker.history(start=date_str, end=end_str)
        if not hist.empty:
            return float(hist['Close'].iloc[0])
    except Exception as e:
        print(f"Error fetching historical exchange rate for {date_str}: {e}")
    return get_exchange_rate()

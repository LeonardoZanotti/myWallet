import yfinance as yf

def get_current_prices(assets):
    """
    Fetches the current market price for a list of assets.
    Returns a dictionary: { 'TICKER': price, ... }
    """
    if not assets:
        return {}
        
    prices = {}
    brl_categories = ['BDR', 'FII', 'Ações', 'BR ETFs', 'BR ETF']
    
    try:
        for asset in assets:
            ticker = asset['ticker']
            tag = asset.get('tag', '')
            
            query_ticker = ticker
            if tag in brl_categories and not ticker.endswith('.SA'):
                query_ticker = ticker + '.SA'
                
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

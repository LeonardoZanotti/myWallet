import yfinance as yf

def get_current_prices(tickers):
    """
    Fetches the current market price for a list of tickers.
    Returns a dictionary: { 'TICKER': price, ... }
    """
    if not tickers:
        return {}
        
    prices = {}
    try:
        # Download data for all tickers, we just need the last close price
        # yf.download can be slow or have issues with single tickers returning a Series instead of DataFrame
        # So it's better to fetch them individually or handle carefully, but Ticker is safer for few assets.
        for ticker in tickers:
            ticker_obj = yf.Ticker(ticker)
            # Use fast_info if available, or history
            try:
                # get history of last 1 day
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

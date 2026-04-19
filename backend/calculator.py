def calculate_smart_buy(assets, current_prices, invest_brl=0.0, invest_usd=0.0):
    """
    assets: list of dicts with 'ticker', 'quantity', 'nota', 'tag'
    current_prices: dict mapping ticker -> price
    invest_brl: float
    invest_usd: float
    
    This splits the BRL investment among assets ending in .SA (or tagged as Brazil),
    and USD investment among the rest. It uses the "nota" to determine the ideal percentage
    within that currency bucket.
    """
    
    # Separate assets by currency bucket
    # Assuming tickers with .SA are BRL, others are USD
    brl_assets = []
    usd_assets = []
    
    for a in assets:
        # Create a copy to not mutate original directly
        asset_copy = dict(a)
        ticker = asset_copy['ticker']
        price = current_prices.get(ticker) or asset_copy.get('average_price', 0)
        
        asset_copy['current_price'] = price
        asset_copy['current_value'] = asset_copy['quantity'] * price
        
        brl_categories = ['BDR', 'FII', 'Ações', 'BR ETFs']
        tag = asset_copy.get('tag', '')
        if tag in brl_categories or ticker.endswith('.SA'):
            brl_assets.append(asset_copy)
        else:
            usd_assets.append(asset_copy)
            
    # Calculate buys for a bucket
    def calculate_for_bucket(bucket_assets, investment_amount):
        if not bucket_assets:
            return []
            
        total_nota = sum(a.get('nota', 0) for a in bucket_assets)
        if total_nota == 0:
            return bucket_assets # Can't distribute
            
        current_total_value = sum(a['current_value'] for a in bucket_assets)
        new_total_value = current_total_value + investment_amount
        
        for a in bucket_assets:
            ideal_percent = a.get('nota', 0) / total_nota
            ideal_value = new_total_value * ideal_percent
            
            value_to_buy = ideal_value - a['current_value']
            # We don't sell in this simple calculator, only buy
            if value_to_buy < 0:
                value_to_buy = 0
                
            a['ideal_percent'] = ideal_percent
            a['value_to_buy'] = value_to_buy
            a['shares_to_buy'] = value_to_buy / a['current_price'] if a['current_price'] > 0 else 0
            
        return bucket_assets

    brl_result = calculate_for_bucket(brl_assets, invest_brl)
    usd_result = calculate_for_bucket(usd_assets, invest_usd)
    
    return brl_result + usd_result

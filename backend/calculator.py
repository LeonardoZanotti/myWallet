def calculate_smart_buy(assets, current_prices, invest_brl=0.0, invest_usd=0.0):
    brl_assets = []
    usd_assets = []
    
    for a in assets:
        asset_copy = dict(a)
        ticker = asset_copy['ticker']
        price = current_prices.get(ticker) or asset_copy.get('average_price', 0)
        
        asset_copy['current_price'] = price
        asset_copy['current_value'] = asset_copy['quantity'] * price
        
        brl_categories = ['BDR', 'FII', 'Ações', 'BR ETFs', 'BR ETF']
        tag = asset_copy.get('tag', '')
        if tag in brl_categories or ticker.endswith('.SA'):
            brl_assets.append(asset_copy)
        else:
            usd_assets.append(asset_copy)
            
    def calculate_for_bucket(bucket_assets, investment_amount):
        if not bucket_assets or investment_amount <= 0:
            for a in bucket_assets:
                a['ideal_percent'] = 0
                a['value_to_buy'] = 0
                a['shares_to_buy'] = 0
            return bucket_assets
            
        total_nota = sum(a.get('nota', 0) for a in bucket_assets)
        if total_nota == 0:
            for a in bucket_assets:
                a['ideal_percent'] = 0
                a['value_to_buy'] = 0
                a['shares_to_buy'] = 0
            return bucket_assets
            
        current_total_value = sum(a['current_value'] for a in bucket_assets)
        new_total_value = current_total_value + investment_amount
        
        total_deficit = 0
        
        # Pass 1: Calculate deficits
        for a in bucket_assets:
            ideal_percent = a.get('nota', 0) / total_nota
            a['ideal_percent'] = ideal_percent
            ideal_value = new_total_value * ideal_percent
            deficit = ideal_value - a['current_value']
            a['deficit'] = deficit if deficit > 0 else 0
            total_deficit += a['deficit']
            
        # Pass 2: Distribute available cash proportionally to deficit
        for a in bucket_assets:
            if total_deficit > 0:
                # We distribute exactly investment_amount based on deficit proportion
                proportion = a['deficit'] / total_deficit
                # If total deficit is less than investment amount, we cap it at deficit
                # Actually, if we invest a massive amount, everyone's deficit becomes large, 
                # but if we just distribute investment_amount proportional to deficit, it converges to ideal.
                value_to_buy = investment_amount * proportion
            else:
                value_to_buy = 0 # pragma: no cover
                
            a['value_to_buy'] = value_to_buy
            a['shares_to_buy'] = value_to_buy / a['current_price'] if a['current_price'] > 0 else 0
            
        return bucket_assets

    brl_result = calculate_for_bucket(brl_assets, invest_brl)
    usd_result = calculate_for_bucket(usd_assets, invest_usd)
    
    return brl_result + usd_result

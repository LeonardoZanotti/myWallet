import math

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
            
    def calculate_for_bucket(bucket_assets, investment_amount, is_brl=False):
        if not bucket_assets or investment_amount <= 0:
            for a in bucket_assets:
                a['ideal_percent'] = 0
                a['value_to_buy'] = 0
                a['shares_to_buy'] = 0
            return bucket_assets, investment_amount
            
        total_nota = sum(a.get('nota', 0) for a in bucket_assets)
        if total_nota == 0:
            for a in bucket_assets:
                a['ideal_percent'] = 0
                a['value_to_buy'] = 0
                a['shares_to_buy'] = 0
            return bucket_assets, investment_amount
            
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
            
        # Pass 2: Distribute available cash
        if not is_brl:
            for a in bucket_assets:
                if total_deficit > 0:
                    proportion = a['deficit'] / total_deficit
                    value_to_buy = investment_amount * proportion
                else:
                    value_to_buy = 0 # pragma: no cover
                    
                a['value_to_buy'] = value_to_buy
                a['shares_to_buy'] = value_to_buy / a['current_price'] if a['current_price'] > 0 else 0
                
            return bucket_assets, 0.0
        else:
            allocated_cash = 0
            for a in bucket_assets:
                if total_deficit > 0:
                    proportion = a['deficit'] / total_deficit
                    value_to_buy = investment_amount * proportion
                else:
                    value_to_buy = 0
                
                shares_to_buy = math.floor(value_to_buy / a['current_price']) if a['current_price'] > 0 else 0
                a['shares_to_buy'] = shares_to_buy
                a['value_to_buy'] = shares_to_buy * a['current_price']
                allocated_cash += a['value_to_buy']
                
            remaining_cash = investment_amount - allocated_cash
            
            while True:
                best_asset = None
                max_remaining_deficit = -1
                
                for a in bucket_assets:
                    if a['current_price'] <= 0 or a['current_price'] > remaining_cash:
                        continue
                        
                    ideal_value = new_total_value * a['ideal_percent']
                    current_allocation = a['current_value'] + a['value_to_buy']
                    remaining_deficit = ideal_value - current_allocation
                    
                    if remaining_deficit > max_remaining_deficit:
                        max_remaining_deficit = remaining_deficit
                        best_asset = a
                        
                if best_asset is None:
                    break
                    
                best_asset['shares_to_buy'] += 1
                best_asset['value_to_buy'] += best_asset['current_price']
                remaining_cash -= best_asset['current_price']
                
            return bucket_assets, remaining_cash

    brl_result, leftover_brl = calculate_for_bucket(brl_assets, invest_brl, is_brl=True)
    usd_result, leftover_usd = calculate_for_bucket(usd_assets, invest_usd, is_brl=False)
    
    return brl_result + usd_result, leftover_brl, leftover_usd

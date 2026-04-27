import math

def calculate_smart_buy(assets, current_prices, invest_brl=0.0, invest_usd=0.0, groups_config=None):
    if groups_config is None:
        groups_config = {}
        
    brl_assets = []
    usd_assets = []
    
    for a in assets:
        asset_copy = dict(a)
        ticker = asset_copy['ticker']
        price = current_prices.get(ticker) or asset_copy.get('average_price', 0)
        
        asset_copy['current_price'] = price
        asset_copy['current_value'] = asset_copy['quantity'] * price
        
        brl_categories = ['BDR', 'FII', 'Ações', 'BR ETFs', 'BR ETF']
        tag = asset_copy.get('tag', 'Outros')
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
            
        current_total_value = sum(a['current_value'] for a in bucket_assets)
        new_total_value = current_total_value + investment_amount
        
        # Step 1: Group Assets
        groups = {}
        for a in bucket_assets:
            tag = a.get('tag', 'Outros')
            if tag not in groups:
                groups[tag] = {'assets': [], 'current_value': 0, 'total_asset_nota': 0}
            groups[tag]['assets'].append(a)
            groups[tag]['current_value'] += a['current_value']
            groups[tag]['total_asset_nota'] += a.get('nota', 0)
            
        # Step 2: Determine Group Weights (Nota)
        total_group_nota = 0
        for tag, g_data in groups.items():
            g_target = groups_config.get(tag, {}).get('target_percent', None)
            if g_target is not None:
                g_data['nota'] = float(g_target)
            else:
                g_data['nota'] = 50.0 # Default group nota
            total_group_nota += g_data['nota']
            
        if total_group_nota == 0:
            for a in bucket_assets:
                a['ideal_percent'] = 0
                a['value_to_buy'] = 0
                a['shares_to_buy'] = 0
            return bucket_assets, investment_amount
            
        # Step 3: Calculate Group Deficits and Distribute Cash to Groups
        total_group_deficit = 0
        for tag, g_data in groups.items():
            g_data['ideal_percent'] = g_data['nota'] / total_group_nota
            g_data['ideal_value'] = new_total_value * g_data['ideal_percent']
            deficit = g_data['ideal_value'] - g_data['current_value']
            g_data['deficit'] = deficit if deficit > 0 else 0
            total_group_deficit += g_data['deficit']
            
        for tag, g_data in groups.items():
            if total_group_deficit > 0:
                g_data['cash_to_invest'] = investment_amount * (g_data['deficit'] / total_group_deficit)
            else:  # pragma: no cover
                g_data['cash_to_invest'] = 0
                
        # Step 4: Distribute Group Cash to Assets within the group
        for tag, g_data in groups.items():
            g_ideal_value = g_data['ideal_value']
            g_total_asset_nota = g_data['total_asset_nota']
            
            g_total_asset_deficit = 0
            for a in g_data['assets']:
                if g_total_asset_nota > 0:
                    a['ideal_percent'] = (a.get('nota', 0) / g_total_asset_nota) * g_data['ideal_percent']
                    a['ideal_value'] = g_ideal_value * (a.get('nota', 0) / g_total_asset_nota)
                else:
                    a['ideal_percent'] = 0
                    a['ideal_value'] = 0
                    
                deficit = a['ideal_value'] - a['current_value']
                a['deficit'] = deficit if deficit > 0 else 0
                g_total_asset_deficit += a['deficit']
                
            for a in g_data['assets']:
                if g_total_asset_deficit > 0:
                    a['value_to_buy_fractional'] = g_data['cash_to_invest'] * (a['deficit'] / g_total_asset_deficit)
                else:
                    a['value_to_buy_fractional'] = 0 # pragma: no cover
                    
        # Step 5: Finalize Fractional or Integer Shares across ALL bucket assets
        if not is_brl:
            for a in bucket_assets:
                a['value_to_buy'] = a['value_to_buy_fractional']
                a['shares_to_buy'] = a['value_to_buy'] / a['current_price'] if a['current_price'] > 0 else 0
            return bucket_assets, 0.0
        else:
            allocated_cash = 0
            for a in bucket_assets:
                shares_to_buy = math.floor(a['value_to_buy_fractional'] / a['current_price']) if a['current_price'] > 0 else 0
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
                        
                    current_allocation = a['current_value'] + a['value_to_buy']
                    remaining_deficit = a['ideal_value'] - current_allocation
                    
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
    
    # Cleanup temporary keys
    for a in brl_result + usd_result:
        for k in ['value_to_buy_fractional', 'ideal_value', 'deficit']:
            if k in a:
                del a[k]
                
    return brl_result + usd_result, leftover_brl, leftover_usd

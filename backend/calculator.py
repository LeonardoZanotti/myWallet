import math

def calculate_smart_buy(assets, current_prices, invest_brl=0.0, invest_usd=0.0, groups_config=None, exchange_rate=5.0):
    if groups_config is None:
        groups_config = {}
        
    groups = {}
    current_total_wallet_brl = 0

    # Step 1: Initialize assets, prices, currency, and group them
    for a in assets:
        asset_copy = dict(a)
        ticker = asset_copy['ticker']
        price = current_prices.get(ticker) or asset_copy.get('average_price', 0)
        
        asset_copy['current_price'] = price
        asset_copy['current_value_native'] = asset_copy['quantity'] * price
        
        brl_categories = ['BDR', 'FII', 'Ações', 'BR ETFs', 'BR ETF']
        tag = asset_copy.get('tag', 'Outros')
        
        is_brl = tag in brl_categories or ticker.endswith('.SA')
        asset_copy['currency'] = 'BRL' if is_brl else 'USD'
        
        asset_copy['current_value_brl'] = asset_copy['current_value_native'] if is_brl else asset_copy['current_value_native'] * exchange_rate
        current_total_wallet_brl += asset_copy['current_value_brl']
        
        if tag not in groups:
            groups[tag] = {'assets': [], 'current_value_brl': 0, 'total_asset_nota': 0, 'currency': asset_copy['currency']}
        
        groups[tag]['assets'].append(asset_copy)
        groups[tag]['current_value_brl'] += asset_copy['current_value_brl']
        groups[tag]['total_asset_nota'] += float(asset_copy.get('nota', 0))

    if not assets or (invest_brl <= 0 and invest_usd <= 0):
        for a in assets:
            a['ideal_percent'] = 0
            a['value_to_buy'] = 0
            a['shares_to_buy'] = 0
        return assets, invest_brl, invest_usd

    # Step 2: Global Ideal Values
    new_total_wallet_brl = current_total_wallet_brl + invest_brl + (invest_usd * exchange_rate)
    
    total_wallet_target = 0
    for tag in groups:
        target = groups_config.get(tag, {}).get('target_percent')
        groups[tag]['target_percent'] = float(target) if target is not None else 0.0
        total_wallet_target += groups[tag]['target_percent']
        
    if total_wallet_target == 0:
        total_wallet_target = len(groups) * 50.0
        for tag in groups:
            groups[tag]['target_percent'] = 50.0

    for tag, g_data in groups.items():
        g_data['ideal_percent'] = g_data['target_percent'] / total_wallet_target
        g_data['ideal_value_brl'] = new_total_wallet_brl * g_data['ideal_percent']
        deficit_brl = g_data['ideal_value_brl'] - g_data['current_value_brl']
        g_data['deficit_brl'] = max(0, deficit_brl)

    # Step 3: Distribute cash by currency bucket deficits
    total_brl_deficit = sum(g['deficit_brl'] for g in groups.values() if g['currency'] == 'BRL')
    total_usd_deficit_brl = sum(g['deficit_brl'] for g in groups.values() if g['currency'] == 'USD')

    for tag, g_data in groups.items():
        if g_data['currency'] == 'BRL':
            if total_brl_deficit > 0:
                g_data['cash_to_invest_native'] = invest_brl * (g_data['deficit_brl'] / total_brl_deficit)
            else:
                g_data['cash_to_invest_native'] = 0
        else: # USD
            if total_usd_deficit_brl > 0:
                usd_deficit_native = g_data['deficit_brl'] / exchange_rate
                total_usd_deficit_native = total_usd_deficit_brl / exchange_rate
                g_data['cash_to_invest_native'] = invest_usd * (usd_deficit_native / total_usd_deficit_native)
            else:
                g_data['cash_to_invest_native'] = 0

    # Step 4: Asset level allocation
    result = []
    for tag, g_data in groups.items():
        g_total_asset_nota = g_data['total_asset_nota']
        g_ideal_value_brl = g_data['ideal_value_brl']
        
        g_total_asset_deficit_native = 0
        for a in g_data['assets']:
            if g_total_asset_nota > 0:
                a_pct_in_group = a.get('nota', 0) / g_total_asset_nota
                a['ideal_percent'] = a_pct_in_group * g_data['ideal_percent']
                a_ideal_value_brl = g_ideal_value_brl * a_pct_in_group
            else:
                a['ideal_percent'] = 0
                a_ideal_value_brl = 0
                
            a_ideal_value_native = a_ideal_value_brl if a['currency'] == 'BRL' else a_ideal_value_brl / exchange_rate
            a['ideal_value_native'] = a_ideal_value_native
            
            deficit_native = a_ideal_value_native - a['current_value_native']
            a['deficit_native'] = max(0, deficit_native)
            g_total_asset_deficit_native += a['deficit_native']
            
        for a in g_data['assets']:
            if g_total_asset_deficit_native > 0:
                a['value_to_buy_fractional'] = g_data['cash_to_invest_native'] * (a['deficit_native'] / g_total_asset_deficit_native)
            else:
                a['value_to_buy_fractional'] = 0
            result.append(a)

    # Step 5: Finalize shares
    remaining_brl = invest_brl
    remaining_usd = invest_usd
    
    brl_assets = [a for a in result if a['currency'] == 'BRL']
    usd_assets = [a for a in result if a['currency'] == 'USD']
    
    allocated_brl = 0
    for a in brl_assets:
        shares_to_buy = math.floor(a['value_to_buy_fractional'] / a['current_price']) if a['current_price'] > 0 else 0
        a['shares_to_buy'] = shares_to_buy
        a['value_to_buy'] = shares_to_buy * a['current_price']
        allocated_brl += a['value_to_buy']
        
    remaining_brl -= allocated_brl
    
    while True:
        best_asset = None
        max_remaining_deficit = -1
        
        for a in brl_assets:
            if a['current_price'] <= 0 or a['current_price'] > remaining_brl:
                continue
            
            current_allocation = a['current_value_native'] + a['value_to_buy']
            remaining_deficit = a['ideal_value_native'] - current_allocation
            
            if remaining_deficit > max_remaining_deficit:
                max_remaining_deficit = remaining_deficit
                best_asset = a
                
        if best_asset is None:
            break
            
        best_asset['shares_to_buy'] += 1
        best_asset['value_to_buy'] += best_asset['current_price']
        remaining_brl -= best_asset['current_price']
        
    for a in usd_assets:
        a['value_to_buy'] = a['value_to_buy_fractional']
        a['shares_to_buy'] = a['value_to_buy'] / a['current_price'] if a['current_price'] > 0 else 0
        remaining_usd -= a['value_to_buy']
        
    for a in result:
        a['current_value'] = a['current_value_native']
        for k in ['current_value_native', 'current_value_brl', 'deficit_brl', 'deficit_native', 'ideal_value_native', 'value_to_buy_fractional']:
            if k in a:
                del a[k]
                
    return result, remaining_brl, remaining_usd

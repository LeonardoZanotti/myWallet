class ValidationError(ValueError):
    pass


def _require_mapping(data, message='Invalid JSON payload.'):
    if not isinstance(data, dict):
        raise ValidationError(message)
    return data


def _to_float(value, field_name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValidationError(f'{field_name} must be a number.')


def _to_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f'{field_name} must be an integer.')


def validate_asset_payload(data, partial=False):
    data = _require_mapping(data)
    cleaned = {}
    required_fields = ['ticker', 'weight', 'tag']

    if not partial:
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValidationError(f'Missing required fields: {", ".join(missing)}.')

    if 'ticker' in data:
        ticker = str(data.get('ticker', '')).strip().upper()
        if not ticker:
            raise ValidationError('Ticker is required.')
        cleaned['ticker'] = ticker


    if 'weight' in data:
        weight = _to_int(data.get('weight'), 'weight')
        if weight < 0 or weight > 100:
            raise ValidationError('Weight must be between 0 and 100.')
        cleaned['weight'] = weight

    if 'tag' in data:
        tag = str(data.get('tag', '')).strip()
        if not tag:
            raise ValidationError('Category is required.')
        cleaned['tag'] = tag

    if 'manual_price' in data:
        manual_price = data.get('manual_price')
        if manual_price in ('', None):
            cleaned['manual_price'] = None
        else:
            manual_price = _to_float(manual_price, 'manual_price')
            if manual_price < 0:
                raise ValidationError('Manual price must be zero or greater.')
            cleaned['manual_price'] = manual_price

    return cleaned


def validate_group_payload(data):
    data = _require_mapping(data)
    if 'target_percent' not in data:
        raise ValidationError('target_percent is required.')

    value = data.get('target_percent')
    if value in ('', None):
        return {'target_percent': None}

    target_percent = _to_float(value, 'target_percent')
    if target_percent < 0:
        raise ValidationError('Group target must be zero or greater.')
    return {'target_percent': target_percent}


def validate_investment_payload(data):
    data = _require_mapping(data)
    invest_brl = _to_float(data.get('invest_brl', 0), 'invest_brl')
    invest_usd = _to_float(data.get('invest_usd', 0), 'invest_usd')
    if invest_brl < 0 or invest_usd < 0:
        raise ValidationError('Investment amounts must be zero or greater.')
    return {'invest_brl': invest_brl, 'invest_usd': invest_usd}


import datetime

def validate_transaction_payload(data):
    data = _require_mapping(data)
    cleaned = {}
    required_fields = ['ticker', 'date', 'type', 'price']
    
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise ValidationError(f'Missing required fields: {", ".join(missing)}.')

    ticker = str(data.get('ticker', '')).strip().upper()
    if not ticker:
        raise ValidationError('Ticker is required.')
    cleaned['ticker'] = ticker

    date_str = str(data.get('date', '')).strip()
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        cleaned['date'] = date_str
    except ValueError:
        raise ValidationError('Date must be in YYYY-MM-DD format.')

    tx_type = str(data.get('type', '')).strip().upper()
    if tx_type not in ('BUY', 'SELL'):
        raise ValidationError('Type must be BUY or SELL.')
    cleaned['type'] = tx_type

    price = _to_float(data.get('price'), 'price')
    if price < 0:
        raise ValidationError('Price must be zero or greater.')
    cleaned['price'] = price

    amount = None
    if 'amount' in data and data.get('amount') not in ('', None):
        amount = _to_float(data.get('amount'), 'amount')
        if amount <= 0:
            raise ValidationError('Amount must be greater than zero.')

    quantity = None
    if 'quantity' in data and data.get('quantity') not in ('', None):
        quantity = _to_float(data.get('quantity'), 'quantity')
        if quantity <= 0:
            raise ValidationError('Quantity must be greater than zero.')

    if quantity is None and amount is None:
        raise ValidationError('Either quantity or amount is required.')

    if quantity is None:
        if price <= 0:
            raise ValidationError('Price must be greater than zero when amount is used.')
        quantity = amount / price

    cleaned['quantity'] = quantity
    cleaned['amount'] = amount if amount is not None else quantity * price

    if 'currency' in data and data.get('currency') not in ('', None):
        currency = str(data.get('currency', '')).strip().upper()
        if currency not in ('BRL', 'USD'):
            raise ValidationError('Currency must be BRL or USD.')
        cleaned['currency'] = currency

    if 'tag' in data and data.get('tag') not in ('', None):
        tag = str(data.get('tag', '')).strip()
        if not tag:
            raise ValidationError('Category is required.')
        cleaned['tag'] = tag

    if 'weight' in data and data.get('weight') not in ('', None):
        weight = _to_int(data.get('weight'), 'weight')
        if weight < 0 or weight > 100:
            raise ValidationError('Weight must be between 0 and 100.')
        cleaned['weight'] = weight

    if 'historical_fx' in data and data.get('historical_fx') not in ('', None):
        historical_fx = _to_float(data.get('historical_fx'), 'historical_fx')
        if historical_fx <= 0:
            raise ValidationError('Historical FX must be greater than zero.')
        cleaned['historical_fx'] = historical_fx

    return cleaned

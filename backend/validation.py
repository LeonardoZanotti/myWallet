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
    required_fields = ['ticker', 'quantity', 'average_price', 'nota', 'tag']

    if not partial:
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValidationError(f'Missing required fields: {", ".join(missing)}.')

    if 'ticker' in data:
        ticker = str(data.get('ticker', '')).strip().upper()
        if not ticker:
            raise ValidationError('Ticker is required.')
        cleaned['ticker'] = ticker

    if 'quantity' in data:
        quantity = _to_float(data.get('quantity'), 'quantity')
        if quantity < 0:
            raise ValidationError('Quantity must be zero or greater.')
        cleaned['quantity'] = quantity

    if 'average_price' in data:
        average_price = _to_float(data.get('average_price'), 'average_price')
        if average_price < 0:
            raise ValidationError('Average price must be zero or greater.')
        cleaned['average_price'] = average_price

    if 'nota' in data:
        nota = _to_int(data.get('nota'), 'nota')
        if nota < 0 or nota > 100:
            raise ValidationError('Nota must be between 0 and 100.')
        cleaned['nota'] = nota

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


def validate_csv_import_payload(data):
    data = _require_mapping(data)
    csv_text = data.get('csv_text')
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise ValidationError('csv_text is required.')

    replace_existing = bool(data.get('replace_existing', False))
    return {'csv_text': csv_text, 'replace_existing': replace_existing}

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from .wallet import load_wallet, add_asset, update_asset, remove_asset, update_group
    from .finance import get_current_prices, get_exchange_rate
    from .calculator import calculate_smart_buy
    from .validation import ValidationError, validate_asset_payload, validate_group_payload, validate_investment_payload
except ImportError:  # pragma: no cover
    from wallet import load_wallet, add_asset, update_asset, remove_asset, update_group
    from finance import get_current_prices, get_exchange_rate
    from calculator import calculate_smart_buy
    from validation import ValidationError, validate_asset_payload, validate_group_payload, validate_investment_payload

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)

BRL_CATEGORIES = ['BDR', 'FII', 'Ações', 'BR ETFs', 'BR ETF']


def json_error(message, status_code=400):
    return jsonify({"error": message}), status_code


def detect_currency(asset):
    tag = asset.get('tag', '')
    ticker = asset.get('ticker', '')
    return 'BRL' if tag in BRL_CATEGORIES or ticker.endswith('.SA') else 'USD'


def enrich_asset(asset, prices):
    enriched = dict(asset)
    enriched['currency'] = detect_currency(asset)
    current_price = prices.get(asset['ticker'])
    enriched['current_price'] = current_price

    if current_price is not None:
        enriched['variation'] = ((current_price - asset['average_price']) / asset['average_price']) * 100 if asset['average_price'] > 0 else 0
        enriched['total_value'] = asset['quantity'] * current_price
    else:
        enriched['variation'] = 0
        enriched['total_value'] = asset['quantity'] * asset['average_price']

    return enriched


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/api/wallet', methods=['GET'])
def get_wallet():
    wallet = load_wallet()
    prices = get_current_prices(wallet['assets'])
    exchange_rate = get_exchange_rate()

    assets = [enrich_asset(asset, prices) for asset in wallet['assets']]

    return jsonify({
        "assets": assets,
        "groups": wallet.get('groups', {}),
        "exchange_rate": exchange_rate
    })


@app.route('/api/wallet/asset', methods=['POST'])
def create_asset():
    try:
        asset_data = validate_asset_payload(request.json or {})
    except ValidationError as exc:
        return json_error(str(exc))

    asset = add_asset(asset_data)
    return jsonify(asset)


@app.route('/api/wallet/asset/<ticker>', methods=['PUT'])
def edit_asset(ticker):
    try:
        update_data = validate_asset_payload(request.json or {}, partial=True)
    except ValidationError as exc:
        return json_error(str(exc))

    asset = update_asset(ticker, update_data)
    if asset is None:
        return json_error('Asset not found.', 404)
    return jsonify(asset)


@app.route('/api/wallet/asset/<ticker>', methods=['DELETE'])
def delete_asset(ticker):
    removed = remove_asset(ticker)
    if not removed:
        return json_error('Asset not found.', 404)
    return jsonify({"status": "success"})


@app.route('/api/wallet/group/<tag>', methods=['PUT'])
def edit_group(tag):
    try:
        update_data = validate_group_payload(request.json or {})
    except ValidationError as exc:
        return json_error(str(exc))

    group = update_group(tag, update_data)
    return jsonify(group)


@app.route('/api/smart-buy', methods=['POST'])
def smart_buy():
    try:
        investment = validate_investment_payload(request.json or {})
    except ValidationError as exc:
        return json_error(str(exc))

    wallet = load_wallet()
    prices = get_current_prices(wallet['assets'])

    assets = []
    for asset in wallet['assets']:
        enriched = dict(asset)
        enriched['currency'] = detect_currency(asset)
        assets.append(enriched)

    exchange_rate = get_exchange_rate()

    result, leftover_brl, leftover_usd = calculate_smart_buy(
        assets,
        prices,
        investment['invest_brl'],
        investment['invest_usd'],
        wallet.get('groups', {}),
        exchange_rate
    )
    return jsonify({
        "recommendations": result,
        "leftover_brl": leftover_brl,
        "leftover_usd": leftover_usd
    })


if __name__ == '__main__':  # pragma: no cover
    app.run(debug=True, port=5000)

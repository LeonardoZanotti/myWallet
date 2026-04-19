from flask import Flask, jsonify, request
from flask_cors import CORS
from wallet import load_wallet, save_wallet, add_asset, update_asset, remove_asset
from finance import get_current_prices
from calculator import calculate_smart_buy

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/wallet', methods=['GET'])
def get_wallet():
    wallet = load_wallet()
    prices = get_current_prices(wallet['assets'])
    
    for a in wallet['assets']:
        a['current_price'] = prices.get(a['ticker'])
        if a['current_price']:
            a['variation'] = ((a['current_price'] - a['average_price']) / a['average_price']) * 100 if a['average_price'] > 0 else 0
            a['total_value'] = a['quantity'] * a['current_price']
        else:
            a['variation'] = 0
            a['total_value'] = a['quantity'] * a['average_price']
            
    return jsonify(wallet)

@app.route('/api/wallet/asset', methods=['POST'])
def create_asset():
    data = request.json
    asset = add_asset(data)
    return jsonify(asset)

@app.route('/api/wallet/asset/<ticker>', methods=['PUT'])
def edit_asset(ticker):
    data = request.json
    asset = update_asset(ticker, data)
    return jsonify(asset)

@app.route('/api/wallet/asset/<ticker>', methods=['DELETE'])
def delete_asset(ticker):
    remove_asset(ticker)
    return jsonify({"status": "success"})

@app.route('/api/smart-buy', methods=['POST'])
def smart_buy():
    data = request.json
    invest_brl = data.get('invest_brl', 0)
    invest_usd = data.get('invest_usd', 0)
    
    wallet = load_wallet()
    prices = get_current_prices(wallet['assets'])
    
    result = calculate_smart_buy(wallet['assets'], prices, invest_brl, invest_usd)
    return jsonify({"recommendations": result})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

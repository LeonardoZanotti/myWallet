# myWallet

`myWallet` is a local portfolio tracker with a Flask backend, a vanilla JavaScript frontend, live Yahoo Finance prices, and a smart-buy calculator that recommends where to invest new BRL and USD cash.

The project now includes:

- deterministic backend tests
- executable frontend behavior tests for add/edit/group/smart-buy flows
- 100% backend coverage
- a wiki with the calculation rules behind every summary, row, column, and smart-buy recommendation

## Stack

- Backend: Flask, `flask-cors`, `yfinance`, `pandas`
- Frontend: HTML, CSS, vanilla JavaScript, Tailwind CDN, Chart.js CDN
- Storage: local JSON file at `backend/wallet.json`
- Tests: `pytest` for Python, `node` for frontend behavior checks

## Requirements

- Python 3.10+
- `pip`
- Node.js 12+ for the frontend behavior tests

## Quick Start

```bash
chmod +x run.sh
./run.sh
```

`run.sh` will:

1. install Python dependencies from `requirements.txt`
2. run the frontend behavior tests with Node
3. run the Python test suite with `pytest`
4. start the Flask server on `http://localhost:5000`

## Manual Start

Install dependencies:

```bash
pip3 install -r requirements.txt
```

Run tests:

```bash
node tests/frontend.spec.js
python3 -m pytest tests/
```

Start the app:

```bash
cd backend
python3 app.py
```

Then open `http://localhost:5000`.

## Main Features

- Track BRL and USD assets in one wallet
- Store assets and group targets locally
- Fetch current prices and USD/BRL exchange rate from Yahoo Finance
- View grouped wallet totals, returns, and allocation percentages
- Edit individual assets and group target percentages from the UI
- Calculate a smart buy plan for BRL and USD cash independently

## Project Structure

- `backend/app.py`: Flask routes and API wiring
- `backend/calculator.py`: smart-buy allocation algorithm
- `backend/finance.py`: Yahoo Finance price and FX lookups
- `backend/wallet.py`: JSON persistence helpers
- `frontend/index.html`: UI structure
- `frontend/app.js`: rendering, forms, modal flows, smart-buy UI logic
- `tests/`: backend tests plus frontend behavior harness
- `wiki/README.md`: detailed software and calculation guide

## Notes About Allocation Logic

- Group targets are normalized across all groups that exist in the wallet.
- Asset `nota` values are normalized only inside their own group.
- BRL cash is invested only into BRL assets; USD cash is invested only into USD assets.
- USD recommendations can be fractional shares.
- BRL recommendations are rounded down to whole shares, then a greedy leftover pass tries to spend the remaining BRL on the most under-allocated eligible asset.

That last point means the final smart-buy result can be close to, but not always exactly equal to, the ideal allocation.

## Wiki

The full calculation guide lives at [wiki/README.md](/home/lzanotti/Documents/projects/myWallet/wiki/README.md).

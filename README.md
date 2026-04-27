# myWallet 💼 

A sleek, locally-hosted Smart Portfolio Tracker with live market data and an intelligent buy calculator to keep your investments perfectly balanced.

## Features ✨

- **Live Market Data:** Automatically fetches real-time prices for your assets (US Stocks, ETFs, Brazilian B3 Assets) via Yahoo Finance (`yfinance`) without requiring any API keys.
- **Smart Buy Calculator:** Input how much cash you want to invest (in BRL and/or USD), and the intelligent calculator tells you exactly how many shares to buy of each asset to reach your ideal portfolio weight (Nota 0-100).
- **Custom Categorization:** Tag your assets however you want (e.g., `Crypto ETF`, `US ETF`, `Brazil FIIs`). The dashboard automatically groups and calculates the returns per category.
- **Privacy First (Local Storage):** Your financial data never leaves your machine. Everything is saved locally to `backend/wallet.json`.
- **Premium UI:** A beautiful dark-mode interface built with TailwindCSS and Chart.js, inspired by platforms like Investidor10.

## Requirements 🛠️

- **Python 3.10+** (Required for the backend server)
- `pip` (Python package installer)

## Installation & Setup 🚀

The easiest way to start the application is by using the provided bash script.

1. Clone or download this repository.
2. Navigate to the project directory:
   ```bash
   cd myWallet
   ```
3. Make the runner script executable (if it isn't already):
   ```bash
   chmod +x run.sh
   ```
4. Start the application:
   ```bash
   ./run.sh
   ```

The script will automatically install the necessary Python dependencies (`Flask`, `yfinance`, `pytest`, `pandas`, `flask-cors`), run the tests to ensure the calculations are accurate, start the local backend server, and open your default browser to `http://localhost:5000`.

## Manual Start ⚙️

If you prefer to start the server manually without the script:

1. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
2. Start the Flask server:
   ```bash
   cd backend
   python3 app.py
   ```
3. Open your browser and navigate to `http://localhost:5000`.

## Testing 🧪

The application uses Test-Driven Development (TDD) to ensure the smart buy logic is bulletproof. 

To run the test suite:
```bash
python3 -m pytest tests/
```

## How It Works 🧠

### Adding Assets
When you add an asset, you give it a **Weight (Nota)** from 0 to 100. 
For example, if you have two US ETFs and you assign one a Nota of `70` and the other a Nota of `30`, the application knows your ideal distribution is 70% / 30% for that asset bucket.

### Smart Buy Calculator
1. Enter the total amount you want to invest in BRL or USD.
2. The calculator takes your current asset balances, adds your new investment amount to determine the *new total value*.
3. It then multiplies that new total by your ideal percentages to find out what each asset's value *should* be.
4. **Fractional vs Integer Calculations**:
   - **USD Assets**: Calculates and recommends fractional shares exactly to match the ideal percentage.
   - **BRL Assets**: Calculates optimal share allocations using whole numbers (integers). It iteratively buys integer shares of the asset furthest from its target, avoiding fractional values, mimicking Brazilian broker limitations.
5. The calculator tells you exactly what to buy and returns any leftover cash that couldn't buy a full share.

## Technology Stack 💻
- **Frontend:** HTML5, CSS3, Vanilla JavaScript, TailwindCSS, Chart.js
- **Backend:** Python, Flask, `yfinance`, Pandas
- **Storage:** JSON (`wallet.json`)

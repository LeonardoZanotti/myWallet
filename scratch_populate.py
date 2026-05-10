import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
import backend.wallet as wallet

transactions_data = [
    # PAGE 2 (Screenshot 1)
    ("AUVP11", "BR ETFs", "BUY", 10.00, 134.95, "2026-04-20"),
    ("BIEU39", "BDR", "BUY", 1.00, 65.82, "2026-02-27"),
    ("KNSC11", "FII", "BUY", 4.00, 9.11, "2026-02-25"),
    ("PVBI11", "FII", "BUY", 1.00, 77.55, "2026-02-25"),
    ("KNCA11", "FII", "BUY", 1.00, 98.35, "2026-02-25"),
    ("KNCR11", "FII", "BUY", 1.00, 106.79, "2026-02-25"),
    ("KNRI11", "FII", "BUY", 1.00, 165.80, "2026-02-25"),
    ("TRXF11", "FII", "BUY", 1.00, 93.07, "2026-02-25"),
    ("VISC11", "FII", "BUY", 1.00, 110.82, "2026-02-25"),
    ("XPML11", "FII", "BUY", 1.00, 111.89, "2026-02-25"),
    ("BTLG11", "FII", "BUY", 1.00, 102.91, "2026-02-25"),
    ("HGLG11", "FII", "BUY", 1.00, 157.75, "2026-02-25"),
    ("DUOL34", "BDR", "BUY", 2.00, 18.20, "2026-02-25"),
    ("M1NS34", "BDR", "BUY", 1.00, 52.18, "2026-02-25"),
    ("TMCO34", "BDR", "BUY", 1.00, 78.00, "2026-02-25"),
    ("ROXO34", "BDR", "BUY", 4.00, 13.44, "2026-02-25"),
    ("CRPT11", "BR ETFs", "BUY", 6.00, 12.42, "2026-02-25"),
    ("HODL11", "BR ETFs", "BUY", 1.00, 59.63, "2026-02-25"),
    ("NASD11", "BR ETFs", "BUY", 16.00, 18.19, "2026-02-25"),
    ("IVVB11", "BR ETFs", "BUY", 1.00, 400.90, "2026-02-25"),
    ("WRLD11", "BR ETFs", "BUY", 3.00, 138.40, "2026-02-25"),
    ("AUVP11", "BR ETFs", "BUY", 11.00, 135.00, "2026-02-25"),
    ("NTNS11", "BR ETFs", "BUY", 7.00, 63.06, "2026-02-25"),
    ("AUPO11", "BR ETFs", "BUY", 7.00, 102.76, "2026-02-25"),
    
    # PAGE 1 (Screenshot 2)
    ("CRPT11", "BR ETFs", "SELL", 6.00, 13.36, "2026-04-28"),
    ("HODL11", "BR ETFs", "SELL", 1.00, 63.84, "2026-04-28"),
    ("IVVB11", "BR ETFs", "SELL", 1.00, 400.95, "2026-04-28"),
    ("NASD11", "BR ETFs", "SELL", 16.00, 18.80, "2026-04-28"),
    ("BIEU39", "BDR", "SELL", 1.00, 60.87, "2026-04-28"),
    ("ROXO34", "BDR", "SELL", 4.00, 12.19, "2026-04-28"),
    ("WRLD11", "BR ETFs", "SELL", 3.00, 134.54, "2026-04-28"),
    ("DUOL34", "BDR", "SELL", 2.00, 16.15, "2026-04-28"),
    ("M1NS34", "BDR", "SELL", 1.00, 48.34, "2026-04-28"),
    ("TMCO34", "BDR", "SELL", 1.00, 60.10, "2026-04-28"),
    ("RVLV", "Stocks", "SELL", 1.00, 26.43, "2026-04-28"),
    ("AUPO11", "BR ETFs", "BUY", 5.00, 105.15, "2026-04-28"),
    ("NTNS11", "BR ETFs", "BUY", 5.00, 64.92, "2026-04-28"),
    ("AUVP11", "BR ETFs", "BUY", 9.00, 129.77, "2026-04-28"),
    ("KNCA11", "FII", "BUY", 1.00, 95.52, "2026-04-28"),
    ("TRXF11", "FII", "BUY", 1.00, 91.83, "2026-04-28"),
    ("XPML11", "FII", "BUY", 1.00, 110.64, "2026-04-28"),
    ("HGLG11", "FII", "BUY", 1.00, 156.30, "2026-04-28"),
    ("KNSC11", "FII", "BUY", 10.00, 9.25, "2026-04-28"),
    ("VT", "US ETFs", "BUY", 1.71, 149.84, "2026-04-28"),
    ("IVV", "US ETFs", "BUY", 0.23, 719.70, "2026-04-28"),
    ("QQQ", "US ETFs", "BUY", 0.11, 657.72, "2026-04-28"),
    ("IBIT", "US ETFs", "BUY", 1.08, 43.24, "2026-04-28"),
    ("RVLV", "Stocks", "BUY", 1.00, 27.23, "2026-04-20"),
    ("IBIT", "US ETFs", "BUY", 1.17, 42.62, "2026-04-20"),
    ("VT", "US ETFs", "BUY", 1.11, 150.37, "2026-04-20"),
    ("QQQ", "US ETFs", "BUY", 0.19, 646.78, "2026-04-20"),
    ("IVV", "US ETFs", "BUY", 0.18, 712.10, "2026-04-20"),
    ("AUPO11", "BR ETFs", "BUY", 6.00, 105.13, "2026-04-20"),
    ("NTNS11", "BR ETFs", "BUY", 5.00, 64.58, "2026-04-20")
]

def run():
    # 1. Clear wallet
    wallet.save_wallet({"assets": [], "groups": {}, "transactions": []})
    
    # 2. Add all tags (since wait, add_transaction creates the asset if missing with tag "Ações" which is wrong)
    # We should add the assets first.
    added_tickers = set()
    for t in transactions_data:
        ticker = t[0]
        tag = t[1]
        if ticker not in added_tickers:
            wallet.add_asset({"ticker": ticker, "weight": 10, "tag": tag})
            added_tickers.add(ticker)
            
    # 3. Add transactions in chronological order (or any order, but let's just loop)
    for t in transactions_data:
        wallet.add_transaction({
            "ticker": t[0],
            "type": t[2],
            "quantity": t[3],
            "price": t[4],
            "date": t[5]
        })

    print("Data imported successfully!")

if __name__ == '__main__':
    run()

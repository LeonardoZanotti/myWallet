import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
import backend.wallet as wallet


GROUPS = {
    "Ações": {"target_percent": 30},
    "US ETFs": {"target_percent": 50},
    "BR ETFs": {"target_percent": 40},
    "FII": {"target_percent": 10},
}


CURRENT_ASSETS = [
    {"ticker": "IVV", "quantity": 0.40274378, "average_price": 716.39, "weight": 30, "tag": "US ETFs"},
    {"ticker": "VT", "quantity": 2.82213075, "average_price": 150.05, "weight": 40, "tag": "US ETFs"},
    {"ticker": "QQQ", "quantity": 0.30372505, "average_price": 650.76, "weight": 20, "tag": "US ETFs"},
    {"ticker": "IBIT", "quantity": 2.25652038, "average_price": 42.92, "weight": 10, "tag": "US ETFs"},
    {"ticker": "AUVP11", "quantity": 30.0, "average_price": 133.43, "weight": 38, "tag": "BR ETFs"},
    {"ticker": "AUPO11", "quantity": 18.0, "average_price": 104.23, "weight": 38, "tag": "BR ETFs"},
    {"ticker": "NTNS11", "quantity": 17.0, "average_price": 64.06, "weight": 25, "tag": "BR ETFs"},
    {"ticker": "KNRI11", "quantity": 1, "average_price": 165.8, "weight": 10, "tag": "FII"},
    {"ticker": "HGLG11", "quantity": 2.0, "average_price": 157.03, "weight": 10, "tag": "FII"},
    {"ticker": "XPML11", "quantity": 2.0, "average_price": 111.27, "weight": 10, "tag": "FII"},
    {"ticker": "VISC11", "quantity": 1, "average_price": 110.82, "weight": 10, "tag": "FII"},
    {"ticker": "KNCR11", "quantity": 1, "average_price": 106.79, "weight": 10, "tag": "FII"},
    {"ticker": "BTLG11", "quantity": 1, "average_price": 102.91, "weight": 10, "tag": "FII"},
    {"ticker": "KNCA11", "quantity": 2.0, "average_price": 96.94, "weight": 10, "tag": "FII"},
    {"ticker": "TRXF11", "quantity": 2.0, "average_price": 92.45, "weight": 10, "tag": "FII"},
    {"ticker": "PVBI11", "quantity": 1, "average_price": 77.55, "weight": 10, "tag": "FII"},
    {"ticker": "KNSC11", "quantity": 14.0, "average_price": 9.21, "weight": 10, "tag": "FII"},
]


# Historical buys/sells visible in the Investidor10 screenshots. The active
# holdings reconcile to CURRENT_ASSETS; sold-out tickers remain only here.
TRANSACTIONS_DATA = [
    ("KNSC11", "FII", "BUY", 4.0, 9.11, "2026-02-25"),
    ("PVBI11", "FII", "BUY", 1.0, 77.55, "2026-02-25"),
    ("KNCA11", "FII", "BUY", 1.0, 98.35, "2026-02-25"),
    ("KNCR11", "FII", "BUY", 1.0, 106.79, "2026-02-25"),
    ("KNRI11", "FII", "BUY", 1.0, 165.80, "2026-02-25"),
    ("TRXF11", "FII", "BUY", 1.0, 93.07, "2026-02-25"),
    ("VISC11", "FII", "BUY", 1.0, 110.82, "2026-02-25"),
    ("XPML11", "FII", "BUY", 1.0, 111.89, "2026-02-25"),
    ("BTLG11", "FII", "BUY", 1.0, 102.91, "2026-02-25"),
    ("HGLG11", "FII", "BUY", 1.0, 157.75, "2026-02-25"),
    ("DUOL34", "BDR", "BUY", 2.0, 18.20, "2026-02-25"),
    ("M1NS34", "BDR", "BUY", 1.0, 52.18, "2026-02-25"),
    ("TMCO34", "BDR", "BUY", 1.0, 78.00, "2026-02-25"),
    ("ROXO34", "BDR", "BUY", 4.0, 13.44, "2026-02-25"),
    ("CRPT11", "BR ETFs", "BUY", 6.0, 12.42, "2026-02-25"),
    ("HODL11", "BR ETFs", "BUY", 1.0, 59.63, "2026-02-25"),
    ("NASD11", "BR ETFs", "BUY", 16.0, 18.19, "2026-02-25"),
    ("IVVB11", "BR ETFs", "BUY", 1.0, 400.90, "2026-02-25"),
    ("WRLD11", "BR ETFs", "BUY", 3.0, 138.40, "2026-02-25"),
    ("AUVP11", "BR ETFs", "BUY", 11.0, 135.00, "2026-02-25"),
    ("NTNS11", "BR ETFs", "BUY", 7.0, 63.06, "2026-02-25"),
    ("AUPO11", "BR ETFs", "BUY", 7.0, 102.76, "2026-02-25"),
    ("BIEU39", "BDR", "BUY", 1.0, 65.82, "2026-02-27"),
    ("RVLV", "Stocks", "BUY", 1.0, 27.23, "2026-04-20"),
    ("IBIT", "US ETFs", "BUY", 1.17652038, 42.62, "2026-04-20"),
    ("VT", "US ETFs", "BUY", 1.11213075, 150.37, "2026-04-20"),
    ("QQQ", "US ETFs", "BUY", 0.19372505, 646.78, "2026-04-20"),
    ("IVV", "US ETFs", "BUY", 0.17274378, 712.10, "2026-04-20"),
    ("AUPO11", "BR ETFs", "BUY", 6.0, 105.13, "2026-04-20"),
    ("NTNS11", "BR ETFs", "BUY", 5.0, 64.58, "2026-04-20"),
    ("AUVP11", "BR ETFs", "BUY", 10.0, 134.95, "2026-04-20"),
    ("CRPT11", "BR ETFs", "SELL", 6.0, 13.36, "2026-04-28"),
    ("HODL11", "BR ETFs", "SELL", 1.0, 63.84, "2026-04-28"),
    ("IVVB11", "BR ETFs", "SELL", 1.0, 400.95, "2026-04-28"),
    ("NASD11", "BR ETFs", "SELL", 16.0, 18.80, "2026-04-28"),
    ("BIEU39", "BDR", "SELL", 1.0, 60.87, "2026-04-28"),
    ("ROXO34", "BDR", "SELL", 4.0, 12.19, "2026-04-28"),
    ("WRLD11", "BR ETFs", "SELL", 3.0, 134.54, "2026-04-28"),
    ("DUOL34", "BDR", "SELL", 2.0, 16.15, "2026-04-28"),
    ("M1NS34", "BDR", "SELL", 1.0, 48.34, "2026-04-28"),
    ("TMCO34", "BDR", "SELL", 1.0, 60.10, "2026-04-28"),
    ("RVLV", "Stocks", "SELL", 1.0, 26.43, "2026-04-28"),
    ("AUPO11", "BR ETFs", "BUY", 5.0, 105.208, "2026-04-28"),
    ("NTNS11", "BR ETFs", "BUY", 5.0, 64.94, "2026-04-28"),
    ("AUVP11", "BR ETFs", "BUY", 9.0, 129.82222222222222, "2026-04-28"),
    ("KNCA11", "FII", "BUY", 1.0, 95.53, "2026-04-28"),
    ("TRXF11", "FII", "BUY", 1.0, 91.83, "2026-04-28"),
    ("XPML11", "FII", "BUY", 1.0, 110.65, "2026-04-28"),
    ("HGLG11", "FII", "BUY", 1.0, 156.31, "2026-04-28"),
    ("KNSC11", "FII", "BUY", 10.0, 9.25, "2026-04-28"),
    ("VT", "US ETFs", "BUY", 1.71, 149.84188196491235, "2026-04-28"),
    ("IVV", "US ETFs", "BUY", 0.23, 719.6120470269564, "2026-04-28"),
    ("QQQ", "US ETFs", "BUY", 0.11, 657.7693245363637, "2026-04-28"),
    ("IBIT", "US ETFs", "BUY", 1.08, 43.24681121666668, "2026-04-28"),
]


def tx_currency(tag):
    return "USD" if tag in {"US ETFs", "Stocks", "Crypto"} else "BRL"


def build_transactions():
    transactions = []
    for index, (ticker, tag, tx_type, quantity, price, date) in enumerate(TRANSACTIONS_DATA, start=1):
        transactions.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"myWallet:{index}:{ticker}:{tx_type}:{date}")),
            "ticker": ticker,
            "tag": tag,
            "type": tx_type,
            "quantity": quantity,
            "price": price,
            "amount": quantity * price,
            "currency": tx_currency(tag),
            "date": date,
        })
    return transactions


def run():
    wallet.save_wallet({
        "assets": [dict(asset) for asset in CURRENT_ASSETS],
        "groups": GROUPS,
        "transactions": build_transactions(),
    })
    wallet.load_wallet()
    print("Data imported successfully!")


if __name__ == "__main__":  # pragma: no cover
    run()

import os
import sys

from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import scratch_populate


def test_scratch_populate_recreates_expected_wallet(tmp_path):
    wallet_file = tmp_path / "wallet.json"

    with patch('backend.wallet.WALLET_FILE', str(wallet_file)):
        scratch_populate.run()
        data = scratch_populate.wallet.load_wallet()

    assert len(data["assets"]) == 17
    assert len(data["transactions"]) == 54
    assert data["groups"] == scratch_populate.GROUPS

    by_ticker = {asset["ticker"]: asset for asset in data["assets"]}
    assert by_ticker["VT"]["quantity"] == 2.82213075
    assert by_ticker["VT"]["average_price"] == 150.05
    assert by_ticker["VT"]["weight"] == 40
    assert by_ticker["AUVP11"]["weight"] == 38
    assert by_ticker["KNSC11"]["tag"] == "FII"
    assert "CRPT11" not in by_ticker

    assert scratch_populate.tx_currency("US ETFs") == "USD"
    assert scratch_populate.tx_currency("BR ETFs") == "BRL"

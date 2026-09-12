import json
import os
import sys
import threading
from contextlib import contextmanager

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from werkzeug.serving import make_server

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import backend.app as backend_app
import backend.wallet as wallet_module


@contextmanager
def live_server(app, host="127.0.0.1", port=0):
    server = make_server(host, port, app)
    actual_port = server.server_port
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    try:
        yield f"http://{host}:{actual_port}"
    finally:
        server.shutdown()
        thread.join()


@pytest.fixture
def browser():
    options = Options()
    options.binary_location = "/usr/bin/chromium-browser"
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1440,1600")
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    try:
        yield driver
    finally:
        driver.quit()


@pytest.fixture
def frontend_env(tmp_path, monkeypatch):
    wallet_file = tmp_path / "wallet.json"
    wallet_file.write_text(json.dumps({"assets": [], "groups": {}}, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(wallet_module, "WALLET_FILE", str(wallet_file))
    monkeypatch.setattr(backend_app, "get_exchange_rate", lambda: 5.0)

    price_map = {
        "IVVB11": 105.0,
        "PETR4.SA": 30.0,
        "VOO": 110.0,
    }

    def fake_prices(assets):
        prices = {}
        for asset in assets:
            ticker = asset["ticker"]
            prices[ticker] = price_map.get(ticker)
        return prices

    monkeypatch.setattr(backend_app, "get_current_prices", fake_prices)

    return wallet_file


def wait_for_text(browser, by, selector, text):
    WebDriverWait(browser, 10).until(
        lambda d: text in d.find_element(by, selector).text
    )


def test_add_asset_flow_renders_real_row(browser, frontend_env):
    with live_server(backend_app.app) as url:
        browser.get(url)

        # Add Asset metadata
        browser.find_element(By.ID, "add-ticker").send_keys("ivvb11")
        browser.find_element(By.ID, "add-weight").send_keys("80")
        browser.find_element(By.ID, "add-tag").send_keys("BR ETFs")
        browser.find_element(By.CSS_SELECTOR, "#add-asset-form button[type='submit']").click()

        import time
        # Add Transaction
        browser.execute_script("""
            openTxModal();
            document.getElementById('tx-ticker').value = 'IVVB11';
            document.getElementById('tx-qty').value = '10,5';
            document.getElementById('tx-price').value = '100,0';
            document.getElementById('tx-form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        """)
        time.sleep(1.0)

        wait_for_text(browser, By.ID, "asset-groups-container", "IVVB11")
        wait_for_text(browser, By.ID, "total-brl", "R$")

        container_text = browser.find_element(By.ID, "asset-groups-container").text
        assert "IVVB11" in container_text
        assert "BR ETFs" in container_text


def test_zero_investment_shows_inline_error(browser, frontend_env):
    with live_server(backend_app.app) as url:
        browser.get(url)

        browser.find_element(By.CSS_SELECTOR, "button[onclick='calculateSmartBuy()']").click()

        wait_for_text(browser, By.ID, "app-feedback", "Please enter an amount to invest.")
        assert "Please enter an amount to invest." in browser.find_element(By.ID, "app-feedback").text


def test_smart_buy_modal_opens_for_real(browser, frontend_env):
    frontend_env.write_text(json.dumps({
        "assets": [
            {"ticker": "PETR4.SA", "weight": 100, "tag": "Ações"},
            {"ticker": "VOO", "weight": 100, "tag": "US ETFs"}
        ],
        "groups": {"Ações": {"target_percent": 50}, "US ETFs": {"target_percent": 50}},
        "transactions": [
            {"id": "1", "ticker": "PETR4.SA", "type": "BUY", "quantity": 1, "price": 25, "date": "2026-01-01"},
            {"id": "2", "ticker": "VOO", "type": "BUY", "quantity": 1, "price": 100, "date": "2026-01-01"}
        ]
    }, ensure_ascii=False), encoding="utf-8")

    with live_server(backend_app.app) as url:
        browser.get(url)
        wait_for_text(browser, By.ID, "asset-groups-container", "PETR4.SA")

        browser.find_element(By.ID, "invest-brl").send_keys("100,0")
        browser.find_element(By.ID, "invest-usd").send_keys("10,0")
        browser.find_element(By.CSS_SELECTOR, "button[onclick='calculateSmartBuy()']").click()

        WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located((By.ID, "recommendation-modal"))
        )
        wait_for_text(browser, By.ID, "recommendation-body", "PETR4.SA")
        body_text = browser.find_element(By.ID, "recommendation-body").text
        assert "PETR4.SA" in body_text
        assert "VOO" in body_text


def test_investment_history_tab_shows_ledger(browser, frontend_env):
    frontend_env.write_text(json.dumps({
        "assets": [
            {"ticker": "VOO", "weight": 100, "tag": "US ETFs"}
        ],
        "groups": {"US ETFs": {"target_percent": 100}},
        "transactions": [
            {"id": "1", "ticker": "VOO", "tag": "US ETFs", "type": "BUY", "quantity": 1.5, "price": 100, "amount": 150, "currency": "USD", "date": "2026-04-20"}
        ]
    }, ensure_ascii=False), encoding="utf-8")

    with live_server(backend_app.app) as url:
        browser.get(url)
        wait_for_text(browser, By.ID, "asset-groups-container", "VOO")

        browser.find_element(By.ID, "tab-transactions").click()

        WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located((By.ID, "transactions-view"))
        )
        wait_for_text(browser, By.ID, "transactions-body", "VOO")
        wait_for_text(browser, By.ID, "monthly-history-body", "04/2026")

        chart_data = browser.execute_script("return window.__lastEvolutionChartData")
        assert chart_data["labels"] == ["2026-04"]
        assert chart_data["brlBuys"] == [0]
        assert chart_data["usdBuysInBrl"] == [750]
        assert chart_data["accumulatedData"] == [750]


def test_investment_release_uses_minimal_existing_asset_fields(browser, frontend_env):
    frontend_env.write_text(json.dumps({
        "assets": [
            {"ticker": "VOO", "weight": 100, "tag": "US ETFs"}
        ],
        "groups": {"US ETFs": {"target_percent": 100}},
        "transactions": [
            {"id": "1", "ticker": "VOO", "tag": "US ETFs", "type": "BUY", "quantity": 1, "price": 100, "amount": 100, "currency": "USD", "date": "2026-04-20"}
        ]
    }, ensure_ascii=False), encoding="utf-8")

    with live_server(backend_app.app) as url:
        browser.get(url)
        wait_for_text(browser, By.ID, "asset-groups-container", "VOO")

        browser.find_element(By.ID, "tab-transactions").click()
        WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located((By.ID, "transactions-view"))
        )

        release_line = browser.find_element(By.CSS_SELECTOR, ".release-line")
        assert not release_line.find_elements(By.CSS_SELECTOR, '[data-field="amount"]')
        assert not release_line.find_elements(By.CSS_SELECTOR, '[data-field="currency"]')
        assert not release_line.find_elements(By.CSS_SELECTOR, '[data-field="tag"]')
        assert not release_line.find_elements(By.CSS_SELECTOR, '[data-field="weight"]')

        browser.execute_script("""
            document.getElementById('release-date').value = '2026-05-10';
            document.querySelector('.release-line [data-field="ticker"]').value = 'VOO';
            document.querySelector('.release-line [data-field="price"]').value = '110';
            document.querySelector('.release-line [data-field="quantity"]').value = '2';
            document.getElementById('release-form').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        """)

        wait_for_text(browser, By.ID, "app-feedback", "Monthly contribution saved.")
        wait_for_text(browser, By.ID, "transactions-body", "2026-05-10")

        txs = json.loads(frontend_env.read_text(encoding="utf-8"))["transactions"]
        saved = next(tx for tx in txs if tx["date"] == "2026-05-10")
        assert saved["ticker"] == "VOO"
        assert saved["quantity"] == 2
        assert saved["price"] == 110
        assert saved["amount"] == 220
        assert saved["currency"] == "USD"
        assert "tag" not in saved
        assert "weight" not in saved


def test_adjustment_modal_uses_minimal_existing_asset_fields(browser, frontend_env):
    with live_server(backend_app.app) as url:
        browser.get(url)

        browser.execute_script("openTxModal();")
        WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located((By.ID, "tx-modal"))
        )

        assert not browser.find_elements(By.ID, "tx-amount")
        assert not browser.find_elements(By.ID, "tx-currency")
        assert not browser.find_elements(By.ID, "tx-tag")
        assert not browser.find_elements(By.ID, "tx-weight")


def test_monthly_contribution_chart_displays_brl_and_usd_side_by_side(browser, frontend_env):
    frontend_env.write_text(json.dumps({
        "assets": [
            {"ticker": "PETR4.SA", "weight": 100, "tag": "Ações"},
            {"ticker": "VOO", "weight": 100, "tag": "US ETFs"}
        ],
        "groups": {},
        "transactions": [
            {"id": "1", "ticker": "PETR4.SA", "tag": "Ações", "type": "BUY", "quantity": 10, "price": 10, "amount": 100, "currency": "BRL", "date": "2026-04-20"},
            {"id": "2", "ticker": "VOO", "tag": "US ETFs", "type": "BUY", "quantity": 1, "price": 20, "amount": 20, "currency": "USD", "date": "2026-04-20"}
        ]
    }, ensure_ascii=False), encoding="utf-8")

    with live_server(backend_app.app) as url:
        browser.get(url)
        wait_for_text(browser, By.ID, "asset-groups-container", "PETR4.SA")

        browser.find_element(By.ID, "tab-transactions").click()
        WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located((By.ID, "transactions-view"))
        )

        chart_config = browser.execute_script("return window.__lastEvolutionChartConfig")
        assert chart_config["xStacked"] is False
        assert chart_config["yStacked"] is False
        assert chart_config["datasets"][0]["stack"] is None
        assert chart_config["datasets"][1]["stack"] is None

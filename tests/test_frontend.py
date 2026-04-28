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

        browser.find_element(By.ID, "add-ticker").send_keys("ivvb11")
        browser.find_element(By.ID, "add-qty").send_keys("10,5")
        browser.find_element(By.ID, "add-price").send_keys("100,0")
        browser.find_element(By.ID, "add-nota").send_keys("80")
        browser.find_element(By.ID, "add-tag").send_keys("BR ETFs")
        browser.find_element(By.CSS_SELECTOR, "#add-asset-form button[type='submit']").click()

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
            {"ticker": "PETR4.SA", "quantity": 1, "average_price": 25, "nota": 100, "tag": "Ações"},
            {"ticker": "VOO", "quantity": 1, "average_price": 100, "nota": 100, "tag": "US ETFs"}
        ],
        "groups": {"Ações": {"target_percent": 50}, "US ETFs": {"target_percent": 50}}
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

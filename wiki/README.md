# myWallet Guide

`myWallet` is a local investment wallet dashboard for mixed BRL and USD portfolios. It stores data in `backend/wallet.json`, fetches market prices from Yahoo Finance, renders portfolio/history views in vanilla JavaScript, and calculates smart-buy recommendations for new BRL/USD cash.

## Architecture

- `backend/app.py`: Flask routes and API response assembly.
- `backend/wallet.py`: JSON persistence, transaction normalization, quantity/average-price recalculation, investment summaries.
- `backend/calculator.py`: smart-buy allocation algorithm.
- `backend/finance.py`: Yahoo Finance prices and USD/BRL exchange rate.
- `backend/validation.py`: request validation and type coercion.
- `frontend/index.html`: dashboard structure, tabs, tables, forms, modals.
- `frontend/app.js`: data fetching, rendering, forms, charts, smart-buy modal.
- `scratch_populate.py`: deterministic seed script that recreates the current sample wallet and historical ledger.
- `tests/`: backend, calculator, finance, validation, seed, and Selenium browser tests.

## Data Model

`wallet.json` has three top-level keys:

- `assets`: current holdings only. Sold-out tickers are removed from this list.
- `transactions`: full buy/sell ledger, including sold-out tickers for history.
- `groups`: target weights per asset category.

### Asset

Stored fields:

- `ticker`
- `quantity`
- `average_price`
- `weight`
- `tag`

`quantity` and `average_price` are recalculated from transactions on load and after transaction changes. Values are rounded to 8 decimals to avoid floating-point noise.

### Transaction

Stored fields:

- `id`
- `date`
- `type`: `BUY` or `SELL`
- `ticker`
- `tag`
- `quantity`
- `price`
- `amount`
- `currency`: `BRL` or `USD`

When a transaction has `amount` and `price` but no quantity, quantity is derived as:

`quantity = amount / price`

BUY increases quantity and cost basis. SELL reduces quantity but keeps the existing average-price basis for the remaining shares. If a sale fully closes a position, the asset is pruned from current holdings while the transaction remains in history.

### Currency

An asset is BRL when its `tag` is in `BRL_CATEGORIES` or its ticker ends with `.SA`; otherwise it is USD.

Yahoo Finance lookups append `.SA` for BRL categories when needed. USD assets are queried without suffix.

## API

### `GET /api/wallet`

Returns:

- active assets enriched with `currency`, `current_price`, `variation`, and `total_value`
- `groups`
- `transactions`
- `investment_summary`
- `exchange_rate`

Only current holdings are returned in `assets`; sold-out assets remain visible through `transactions`.

### `POST /api/wallet/asset`

Creates asset metadata or updates an existing ticker's `weight` and `tag`.

### `PUT /api/wallet/asset/<ticker>`

Updates existing asset metadata.

### `DELETE /api/wallet/asset/<ticker>`

Deletes the asset and all of its transactions.

### `POST /api/wallet/transaction`

Adds a BUY/SELL entry and recalculates the affected asset. Payloads may include either `quantity + price` or `amount + price`.

Optional `currency`, `tag`, and `weight` let a new investment line create/update asset metadata at the same time.

### `DELETE /api/wallet/transaction/<id>`

Deletes one ledger entry and recalculates the affected asset.

### `PUT /api/wallet/group/<tag>`

Sets `target_percent` for a category. `null` means no explicit target.

### `POST /api/smart-buy`

Accepts `invest_brl` and `invest_usd`; returns recommendations plus leftover cash.

## Portfolio Calculations

### Price and Value

For each asset:

- `current_price = Yahoo price`, or `average_price` when Yahoo has no price.
- `total_value = quantity * current_price`.
- `variation = ((current_price - average_price) / average_price) * 100`.
- if `average_price` is zero or price is missing, variation is `0`.

### Unified BRL Values

For comparisons across currencies:

- BRL rate: `1`
- USD rate: `exchange_rate`
- `unified_value = total_value * rate`
- `cost_unified = quantity * average_price * rate`

Dashboard cards:

- Total Patrimony: `sum(unified_value)`
- Total BRL Assets: `sum(total_value for BRL assets)`
- Total USD Assets: `sum(total_value for USD assets)`
- Unified Return: `((sum(unified_value) - sum(cost_unified)) / sum(cost_unified)) * 100`

### Group Values

For each group:

- native group value: `sum(asset.total_value)`
- group cost: `sum(quantity * average_price)`
- group return: `((group_value - group_cost) / group_cost) * 100`
- wallet share: `group_unified_value / total_unified_value`

### Asset Allocation Columns

Inside a group:

- actual group share: `asset.total_value / group_value`
- target group share: `asset.weight / sum(group asset weights)`

Inside the whole wallet:

- actual wallet share: `asset.unified_value / total_unified_value`
- normalized group target: `group.target_percent / sum(all visible group targets)`
- target wallet share: `normalized_group_target * target_group_share`

If no group target is set, the UI uses fallback `50` for display normalization. If all calculator targets are absent or zero, the calculator also falls back to equal group weights.

## Investment History

The Investment History tab uses `transactions` and `investment_summary`.

`investment_summary` contains:

- total BUY and SELL amounts by BRL/USD
- gross invested BRL equivalent
- net invested BRL equivalent
- monthly rows
- by-asset totals

Monthly rows include:

- `buy_brl`
- `buy_usd`
- `sell_brl`
- `sell_usd`
- `gross_brl_equivalent`
- `net_brl_equivalent`

The monthly chart uses the same monthly data as the table:

- green bars: BRL buys
- blue bars: USD buys converted to BRL
- amber line: accumulated net invested in BRL equivalent

Selenium tests assert the rendered history and chart data for ledger fixtures.

## Smart-Buy Algorithm

The calculator receives active assets, current prices, BRL cash, USD cash, group targets, and exchange rate.

1. Prepare each asset with current price, native value, BRL-equivalent value, currency, and group.
2. Compute future wallet value:

   `new_total_brl = current_total_brl + invest_brl + invest_usd * exchange_rate`

3. Normalize group targets and compute each group's ideal BRL value:

   `group_ideal_value = new_total_brl * normalized_group_target`

4. Compute group deficits:

   `group_deficit = max(0, group_ideal_value - group_current_value)`

5. Split incoming cash by currency bucket:

   - BRL cash can only buy BRL groups.
   - USD cash can only buy USD groups.
   - if a currency bucket has no deficit, its cash remains leftover.

6. Split each group's cash across assets by asset-level deficits:

   - `asset_target_in_group = asset.weight / group_weight_sum`
   - `asset_ideal_value = group_ideal_value * asset_target_in_group`
   - `asset_deficit = max(0, asset_ideal_value_native - asset_current_value_native)`

7. Convert values to shares:

   - USD assets allow fractional shares.
   - BRL assets are floored to whole shares.
   - remaining BRL cash is greedily spent one share at a time on the most under-allocated eligible BRL asset.

Returned per asset:

- `ticker`
- `tag`
- `currency`
- `current_price`
- `current_value`
- `ideal_percent`
- `value_to_buy`
- `shares_to_buy`

Returned globally:

- `leftover_brl`
- `leftover_usd`

## Frontend Behavior

- The portfolio tab shows current holdings only.
- The investment history tab shows historical ledger entries, including sold-out tickers.
- New Investment Release creates one BUY transaction per line.
- Add Adjustment opens the low-level ledger modal for BUY/SELL fixes.
- Charts expose their source datasets to tests so rendered graph inputs can be verified.
- If Chart.js is unavailable, tables and calculations still render.
- Feedback messages appear inline in `#app-feedback`.

## Seed Data

Run:

```bash
python3 scratch_populate.py
```

This recreates:

- 17 active holdings
- 54 historical transactions
- group targets for `Ações`, `US ETFs`, `BR ETFs`, and `FII`

The seed reconciles active holdings to the current reference wallet while preserving buy/sell history.

## Test and Coverage

Run the normal suite:

```bash
pytest -q
```

Run coverage:

```bash
pytest --cov=backend --cov=scratch_populate --cov-branch --cov-report=term-missing -q
```

Current backend and seed coverage is 100% statement and branch coverage. The suite includes:

- wallet migration, normalization, pruning, summaries, CRUD, edge sells
- validation success/error branches
- smart-buy allocation math and leftovers
- finance price/FX fallbacks
- Flask API routes
- deterministic seed recreation
- Selenium browser flows for portfolio, smart-buy modal, investment history, monthly chart data

Coverage does not prove financial advice correctness, but it does assert the implemented rules above exhaustively for the backend and through representative browser flows for the UI.

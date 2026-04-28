# myWallet Wiki

## 1. What the software does

`myWallet` is a local portfolio manager for mixed BRL and USD portfolios.

It has four main jobs:

1. store wallet data locally in `backend/wallet.json`
2. fetch live prices and USD/BRL FX data
3. render grouped wallet summaries and allocation views
4. calculate a smart-buy recommendation for new BRL and USD cash

## 2. Architecture

### Backend

- `backend/app.py`
  Exposes the HTTP routes used by the frontend.
- `backend/wallet.py`
  Reads and writes the local JSON wallet file.
- `backend/finance.py`
  Queries Yahoo Finance for current prices and the USD/BRL exchange rate.
- `backend/calculator.py`
  Computes the smart-buy recommendation.

### Frontend

- `frontend/index.html`
  Defines the dashboard, forms, chart, and modal shells.
- `frontend/app.js`
  Fetches wallet data, renders tables and summary cards, handles add/edit/delete actions, and renders the smart-buy modal.

## 3. Data model

### Asset fields

Each asset in `wallet.json` is expected to carry:

- `ticker`
- `quantity`
- `average_price`
- `nota`
- `tag`

Derived fields added at runtime include:

- `currency`
- `current_price`
- `variation`
- `total_value`
- `ideal_percent`
- `shares_to_buy`
- `value_to_buy`

### Group fields

Each group is keyed by `tag`.

Supported stored field today:

- `target_percent`

This is the configured group weight before normalization.

## 4. Currency classification

The code treats an asset as BRL when either of these is true:

- `tag` is one of `BDR`, `FII`, `Ações`, `BR ETFs`, `BR ETF`
- `ticker` ends with `.SA`

Otherwise, the asset is treated as USD.

This affects:

- how market data is queried
- whether value stays native or is converted with the exchange rate
- whether smart-buy shares can be fractional

## 5. Backend API

### `GET /api/wallet`

Returns:

- assets with derived `currency`, `current_price`, `variation`, and `total_value`
- saved group configuration
- current exchange rate

### `POST /api/wallet/asset`

Adds a new asset. If the ticker already exists, quantity is merged and average price becomes a weighted average:

`new_average_price = ((old_qty * old_avg) + (new_qty * new_avg)) / (old_qty + new_qty)`

### `PUT /api/wallet/asset/<ticker>`

Overwrites any provided asset fields.

### `DELETE /api/wallet/asset/<ticker>`

Removes the asset.

### `PUT /api/wallet/group/<tag>`

Creates or updates group configuration, currently `target_percent`.

### `POST /api/smart-buy`

Accepts:

- `invest_brl`
- `invest_usd`

Returns:

- `recommendations`
- `leftover_brl`
- `leftover_usd`

## 6. Dashboard calculations

This section explains what every visible metric means.

### Summary cards

#### Total Patrimony (Unified)

Formula:

`sum(asset.total_value * rate)`

Where:

- `rate = 1` for BRL assets
- `rate = exchange_rate` for USD assets

This is the wallet value translated into BRL.

#### Total USD Assets

Formula:

`sum(asset.total_value for USD assets)`

This stays in USD.

#### Total BRL Assets

Formula:

`sum(asset.total_value for BRL assets)`

This stays in BRL.

#### Unified Return

Formula:

`((total_patrimony_unified - total_cost_unified) / total_cost_unified) * 100`

Where:

`total_cost_unified = sum(quantity * average_price * rate)`

If total cost is zero, return is shown as `0`.

### Group card header

Each rendered group shows:

- actual wallet share
- configured target label
- current group value
- group return

#### Group actual wallet share

Formula:

`(group_total_unified / total_patrimony_unified) * 100`

#### Group value

Formula:

`sum(asset.total_value)`

Shown in the group's own currency.

#### Group return

Formula:

`((group_total - group_cost) / group_cost) * 100`

Where:

- `group_total = sum(asset.total_value)`
- `group_cost = sum(quantity * average_price)`

This return is calculated in the group's own currency.

### Asset table columns

#### Asset

Raw `ticker`.

#### Qty

Raw `quantity`.

#### Avg Price

Raw `average_price`, formatted in the asset currency.

#### Current

Current market price from Yahoo Finance. If no price is returned, the UI shows `N/A`.

#### Variation

Formula:

`((current_price - average_price) / average_price) * 100`

If `average_price` is zero or `current_price` is missing, variation is shown as `0`.

#### Value

Formula:

`quantity * current_price`

If `current_price` is missing, backend fallback is:

`quantity * average_price`

#### Weight

Raw asset `nota`.

#### % Group

The column shows two values:

- actual group share
- target share inside the group

Actual formula:

`(asset.total_value / group_total) * 100`

Target formula:

`(asset.nota / total_group_nota) * 100`

If group total or total group nota is zero, the corresponding percentage is `0`.

#### % Wallet

The column also shows two values:

- actual wallet share
- target wallet share

Actual formula:

`(asset_unified_value / total_patrimony_unified) * 100`

Where:

`asset_unified_value = asset.total_value * rate`

Target wallet share formula:

1. normalize each group target across all groups that exist in the wallet
2. multiply that normalized group share by the asset's target share inside the group

Explicitly:

`normalized_group_target = group_target_percent / sum(all_group_target_percents)`

`target_wallet_share = normalized_group_target * (asset.nota / total_group_nota)`

If a group has no configured target, the UI and calculator both treat it as `50` during normalization.

If every group target is absent or null, all groups become equal because each one contributes the same fallback `50`.

## 7. Smart-buy algorithm

The smart-buy logic lives in `backend/calculator.py`.

It runs in five stages.

### Stage 1: prepare asset values

For each asset:

1. pick `current_price`
   - use fetched market price when available
   - otherwise fall back to `average_price`
2. compute native current value
   - `current_value_native = quantity * current_price`
3. detect `currency`
4. compute unified BRL value
   - BRL asset: `current_value_brl = current_value_native`
   - USD asset: `current_value_brl = current_value_native * exchange_rate`
5. accumulate group totals and total wallet value

### Stage 2: compute ideal group values

The calculator first computes the future wallet value:

`new_total_wallet_brl = current_total_wallet_brl + invest_brl + (invest_usd * exchange_rate)`

Then it reads `target_percent` from every group.

Normalization rule:

- configured targets are summed across all existing groups
- missing targets are treated as `0` during this first pass
- if the total ends up as `0`, every group is assigned fallback `50`

For each group:

`group_ideal_percent = group_target_percent / total_wallet_target`

`group_ideal_value_brl = new_total_wallet_brl * group_ideal_percent`

`group_deficit_brl = max(0, group_ideal_value_brl - group_current_value_brl)`

Important nuance:

The ideal portfolio is global, but the money buckets are separate. BRL cash can only buy BRL assets, and USD cash can only buy USD assets. That means a recommendation can still have leftover cash or remain off-target when the available currency does not match the biggest deficit.

### Stage 3: split incoming cash by currency bucket

BRL investment is spread only across BRL groups:

`group_brl_cash = invest_brl * (group_deficit_brl / total_brl_deficit)`

USD investment is spread only across USD groups:

`group_usd_cash = invest_usd * (group_deficit_usd_native / total_usd_deficit_native)`

If a bucket has zero deficit, no cash from that bucket is allocated and it becomes leftover.

### Stage 4: split each group allocation across its assets

Inside each group:

`asset_pct_in_group = asset.nota / total_group_nota`

`asset_ideal_percent = asset_pct_in_group * group_ideal_percent`

`asset_ideal_value_brl = group_ideal_value_brl * asset_pct_in_group`

Convert ideal value back to native currency when needed:

- BRL: `asset_ideal_value_native = asset_ideal_value_brl`
- USD: `asset_ideal_value_native = asset_ideal_value_brl / exchange_rate`

Then compute native deficit:

`asset_deficit_native = max(0, asset_ideal_value_native - asset_current_value_native)`

Group cash is distributed proportionally to those asset deficits:

`asset_value_to_buy_fractional = group_cash_to_invest_native * (asset_deficit_native / total_group_asset_deficit_native)`

If total group nota is zero, the assets in that group get `ideal_percent = 0` and receive no allocation.

### Stage 5: convert allocations into orders

#### USD assets

USD assets stay fractional:

`shares_to_buy = value_to_buy / current_price`

#### BRL assets

BRL assets are converted to whole shares:

1. base pass:
   `shares_to_buy = floor(value_to_buy_fractional / current_price)`
2. leftover pass:
   spend remaining BRL one share at a time on the eligible asset with the largest remaining deficit

The leftover pass stops when:

- no BRL asset has a positive price small enough to fit in the remaining BRL cash
- or no remaining deficit beats the current best candidate

### Returned smart-buy fields

For each recommendation row:

- `ticker`
- `tag`
- `currency`
- `current_price`
- `current_value`
- `ideal_percent`
- `value_to_buy`
- `shares_to_buy`

And globally:

- `leftover_brl`
- `leftover_usd`

## 8. Smart-buy modal calculations

The recommendation modal uses backend results plus frontend display math.

### Current %

Formula:

`(current_unified_value / total_current_recommendation_value_unified) * 100`

### Ideal %

Formula:

`ideal_percent * 100`

### Smart Buy

For BRL:

- buy amount is shown in BRL
- shares are shown as an integer

For USD:

- buy amount is shown in USD
- shares are shown with two decimals

### Post-Inv %

Formula:

`(post_investment_unified_value / new_total_brl) * 100`

Where:

- `post_investment_native_value = current_value + value_to_buy`
- `post_investment_unified_value = post_investment_native_value * rate`
- `new_total_brl = total_current_brl_unified + invest_brl + (invest_usd * exchange_rate)`

### Leftover Cash

Shown only when either leftover value is greater than zero.

## 9. Known behavior and constraints

- If Yahoo Finance returns no current price, the wallet still works by falling back to average price for valuation.
- Group target percentages are relative weights, not absolute final wallet percentages unless they already sum to `100`.
- Setting all group targets to zero does not create a zero-allocation portfolio. The calculator falls back to equal group weights.
- BRL recommendations are intentionally discrete because the algorithm assumes whole-share purchases.
- Mixed-currency targets can be mathematically ideal even when the available new cash is only in one currency.

## 10. Test coverage

The project test suite covers:

- wallet file loading, saving, merging, updates, and deletion
- finance lookups and fallback behavior
- all smart-buy branches in the backend calculator
- Flask routes for wallet and smart-buy APIs
- frontend behavior for:
  - initial wallet load
  - add asset submission
  - group target editing
  - smart-buy modal rendering
  - target percentage display
  - unified chart values

Run everything with:

```bash
node tests/frontend.spec.js
python3 -m pytest tests/
```

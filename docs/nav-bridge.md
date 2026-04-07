# NAV Bridge

The 8-line valuation walk that fund analysts compute every quarter.

## What it is

A NAV bridge reconciles a fund's beginning Net Asset Value (NAV) to its ending NAV by walking through every cash movement and revaluation that happened during the period. It's the primary financial reporting artifact for any private equity fund.

## The 8 lines

```
Beginning NAV          appraiser value at period start
+ Contribution         capital deployed during the period
- Disposition          proceeds received from property sales during the period
+ Income               rental and operating income collected during the period
= Cashflow-Adjusted NAV  intermediate subtotal
- Income Reversal      removes income (income doesn't change property valuation)
+/- Write Up/Down      the plug -- derived to balance to ending NAV
= Ending NAV           appraiser value at period end
```

## The math

Given:

- `B` = beginning NAV (known, from the appraiser)
- `C` = sum of contributions in the period
- `D` = sum of dispositions in the period
- `I` = sum of income in the period
- `E` = ending NAV (known, from the appraiser)

Then:

```
cashflow_adjusted_nav = B + C - D + I
income_reversal       = -I
write_up_down         = E - (cashflow_adjusted_nav + income_reversal)
                      = E - B - C + D - I + I
                      = E - B - C + D
```

The `write_up_down` line is the **plug** -- it absorbs whatever revaluation happened during the period so the bridge balances. Agents must compute it correctly, not just look it up.

## Why income reversal exists

Property valuations from appraisers don't include current-period income. They reflect the underlying asset value, not the cash that's been distributed. So the income that was added on the cashflow side (`+ I`) has to be subtracted on the valuation side (`- I`) to avoid double-counting it when we balance to the appraiser's ending NAV.

## Period semantics

Only cashflows **on or after** the period start date count toward Contribution, Disposition, and Income for the bridge. Earlier cashflows are part of the historical record (used for IRR computation) but don't affect the bridge.

In FundLens, the period starts on `2024-01-01` and ends on each fund's `reporting_date` (typically `2024-12-31`).

## The plug must balance

Every correct bridge satisfies this invariant:

```
cashflow_adjusted_nav + income_reversal + write_up_down == ending_nav
```

The seed data is built so this always holds. The grader checks each line independently with a `±$0.50M` tolerance.

## Example

A simple fund with:

- Beginning NAV: 100.0
- Contributions in period: 20.0
- Dispositions in period: 5.0
- Income in period: 3.0
- Ending NAV (from appraiser): 120.0

The bridge:

| Line                  | Value  |
|-----------------------|--------|
| Beginning NAV         | 100.00 |
| + Contribution        |  20.00 |
| - Disposition         |   5.00 |
| + Income              |   3.00 |
| = Cashflow-Adjusted NAV | 118.00 |
| - Income Reversal     |  -3.00 |
| +/- Write Up/Down     |   5.00 |
| = Ending NAV          | 120.00 |

Sanity check: `118.00 + (-3.00) + 5.00 = 120.00`. Bridge balances.

## Computing it from raw data

Agents can take a shortcut and call `get_nav_bridge(fund_id)` which returns the answer directly. But the more interesting (and harder) path is to compute it from the underlying cashflows:

1. Call `get_deal_info(fund_id)` to get the `fund_beginning_nav`.
2. Call `get_cashflow_summary(fund_id)` to get the period totals.
3. Look up the ending NAV from `get_portfolio_summary`.
4. Compute each line, including the plug.

The hard task adds the wrinkle that some deals are co-invested across multiple funds with `ownership_pct < 1.0`. Agents must apply ownership percentages to the cashflows before aggregating at the fund level.

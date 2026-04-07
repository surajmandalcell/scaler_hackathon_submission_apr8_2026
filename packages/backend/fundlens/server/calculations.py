"""Pure-Python financial calculations for FundLens. No scipy/numpy/pandas.

Cashflow types:
  contribution  — capital deployed (fund_amt negative)
  disposition   — all proceeds received: ROC + G/L + FX G/L combined (fund_amt positive)
  income        — rental / operating income (fund_amt positive)

NAV Bridge (8 lines, fund-level USD):
  Beginning NAV
  + Contribution      (capital deployed → adds to NAV)
  − Disposition       (proceeds received → reduces invested book value)
  + Income            (cashflow impact)
  = CF Adjusted NAV
  − Income Reversal   (remove income from valuation)
  +/− Write Up/Down   ← PLUG: Ending NAV − (CF Adj NAV + Income Reversal)
  = Ending NAV        (appraiser value)
"""
from __future__ import annotations

from datetime import date as date_type

from fundlens.server.data_store import DataStore

# ── NAV Bridge ────────────────────────────────────────────────────────────

def compute_nav_bridge(fund_id: str, store: DataStore) -> dict[str, float]:
    """8-line NAV bridge for a fund (USD millions)."""
    fund = store.funds.get(fund_id)
    if not fund:
        return {}

    all_cfs = store.get_cashflows(fund_id=fund_id)

    # Only period cashflows go into the bridge
    if fund.nav_period_start:
        cfs = [c for c in all_cfs if c.cash_date >= fund.nav_period_start]
    else:
        cfs = all_cfs

    # contribution fund_amt is negative → flip to positive for bridge display
    contribution = -sum(c.fund_amt for c in cfs if c.cf_type == "contribution")
    # disposition fund_amt is positive → shown as positive, subtracted in formula
    disposition  =  sum(c.fund_amt for c in cfs if c.cf_type == "disposition")
    income       =  sum(c.fund_amt for c in cfs if c.cf_type == "income")

    cf_adj_nav      = fund.beginning_nav + contribution - disposition + income
    income_reversal = -income
    write_up_down   = fund.ending_nav - (cf_adj_nav + income_reversal)
    ending_nav      = cf_adj_nav + income_reversal + write_up_down  # == fund.ending_nav

    return {
        "beginning_nav":         round(fund.beginning_nav, 4),
        "contribution":          round(contribution, 4),
        "disposition":           round(disposition, 4),
        "income":                round(income, 4),
        "cashflow_adjusted_nav": round(cf_adj_nav, 4),
        "income_reversal":       round(income_reversal, 4),
        "write_up_down":         round(write_up_down, 4),
        "ending_nav":            round(ending_nav, 4),
    }


# ── XIRR ──────────────────────────────────────────────────────────────────

def calculate_xirr(
    cashflows: list[tuple],   # [(date, amount), ...]
    guess: float = 0.1,
    tol: float = 1e-6,
    max_iter: int = 200,
) -> float:
    """Newton-Raphson XIRR. Pure Python — no scipy.
    cashflows: list of (date, float) where negative = outflow.
    Returns IRR as decimal (0.15 = 15%).
    """
    if not cashflows:
        return 0.0

    dates, amounts = zip(*cashflows)
    t0 = dates[0]

    def year_frac(d: date_type) -> float:
        return (d - t0).days / 365.25

    def npv(rate: float) -> float:
        return sum(
            amt / (1.0 + rate) ** year_frac(d)
            for d, amt in zip(dates, amounts)
        )

    def dnpv(rate: float) -> float:
        return sum(
            -year_frac(d) * amt / (1.0 + rate) ** (year_frac(d) + 1.0)
            for d, amt in zip(dates, amounts)
        )

    rate = guess
    for _ in range(max_iter):
        f  = npv(rate)
        df = dnpv(rate)
        if abs(df) < 1e-12:
            break
        new_rate = rate - f / df
        if abs(new_rate - rate) < tol:
            return new_rate
        rate = new_rate
    return rate


# ── Performance Metrics ───────────────────────────────────────────────────

def compute_metrics(fund_id: str, store: DataStore) -> dict[str, float]:
    """
    Compute MOIC and IRR for a fund (fund-level USD, all historical cashflows).

    MOIC = (total_disposition + total_income + ending_nav) / total_contributions
    IRR  = XIRR on all cashflows + terminal value (ending_nav at reporting_date)
    """
    fund = store.funds.get(fund_id)
    if not fund:
        return {}

    cfs = store.get_cashflows(fund_id=fund_id)

    total_invested     = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
    total_disposition  = sum(c.fund_amt      for c in cfs if c.cf_type == "disposition")
    total_income       = sum(c.fund_amt      for c in cfs if c.cf_type == "income")
    unrealized         = fund.ending_nav

    if total_invested == 0:
        return {}

    moic = (total_disposition + total_income + unrealized) / total_invested

    # IRR: all cashflows + terminal ending NAV
    terminal_date = date_type.fromisoformat(fund.reporting_date)
    irr_map: dict[date_type, float] = {}
    for c in cfs:
        d = date_type.fromisoformat(c.cash_date)
        irr_map[d] = irr_map.get(d, 0.0) + c.fund_amt  # contributions negative, rest positive
    irr_map[terminal_date] = irr_map.get(terminal_date, 0.0) + unrealized
    irr = calculate_xirr(sorted(irr_map.items()))

    return {
        "moic": round(moic, 6),
        "irr":  round(irr, 6),
    }


# ── Portfolio-level (aggregate across all funds) ──────────────────────────

def compute_portfolio_nav_bridge(store: DataStore) -> dict[str, float]:
    """Sum individual fund NAV bridges across all funds in the store."""
    combined: dict[str, float] = {}
    for fid in store.funds:
        bridge = compute_nav_bridge(fid, store)
        for k, v in bridge.items():
            combined[k] = combined.get(k, 0.0) + v
    return {k: round(v, 4) for k, v in combined.items()}


def compute_portfolio_metrics(store: DataStore) -> dict[str, float]:
    """Combined MOIC and IRR across all funds (pooled cashflows)."""
    total_invested    = 0.0
    total_disposition = 0.0
    total_income      = 0.0
    total_ending_nav  = 0.0
    irr_map: dict[date_type, float] = {}

    for fid, fund in store.funds.items():
        cfs = store.get_cashflows(fund_id=fid)
        total_invested    += sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
        total_disposition += sum(c.fund_amt      for c in cfs if c.cf_type == "disposition")
        total_income      += sum(c.fund_amt      for c in cfs if c.cf_type == "income")
        total_ending_nav  += fund.ending_nav
        terminal = date_type.fromisoformat(fund.reporting_date)
        for c in cfs:
            d = date_type.fromisoformat(c.cash_date)
            irr_map[d] = irr_map.get(d, 0.0) + c.fund_amt
        irr_map[terminal] = irr_map.get(terminal, 0.0) + fund.ending_nav

    if total_invested == 0:
        return {}

    moic = (total_disposition + total_income + total_ending_nav) / total_invested
    irr  = calculate_xirr(sorted(irr_map.items()))
    return {"moic": round(moic, 6), "irr": round(irr, 6)}


# ── Deal / Investment level ───────────────────────────────────────────────

def compute_deal_nav_bridge(fund_id: str, deal_id: str, store: DataStore) -> dict[str, float]:
    """8-line NAV bridge for a single deal within a fund.
    beginning_nav is estimated proportionally: fund.beginning_nav × (deal_fund_share / fund.ending_nav).
    All cashflow amounts are already the fund's share (after ownership_pct applied at ingestion)."""
    fund = store.funds.get(fund_id)
    deal = store.deals.get(deal_id)
    if not fund or not deal:
        return {}

    own     = store.get_ownership(fund_id, deal_id)
    own_pct = own.ownership_pct if own else 1.0
    ending_nav = round(deal.appraiser_nav * own_pct, 4)

    # Proportional beginning NAV estimate
    if fund.ending_nav > 0:
        beginning_nav = round(fund.beginning_nav * (ending_nav / fund.ending_nav), 4)
    else:
        beginning_nav = 0.0

    all_cfs = store.get_cashflows(fund_id=fund_id, deal_id=deal_id)
    if fund.nav_period_start:
        cfs = [c for c in all_cfs if c.cash_date >= fund.nav_period_start]
    else:
        cfs = all_cfs

    contribution = -sum(c.fund_amt for c in cfs if c.cf_type == "contribution")
    disposition  =  sum(c.fund_amt for c in cfs if c.cf_type == "disposition")
    income       =  sum(c.fund_amt for c in cfs if c.cf_type == "income")

    cf_adj_nav      = beginning_nav + contribution - disposition + income
    income_reversal = -income
    write_up_down   = ending_nav - (cf_adj_nav + income_reversal)

    return {
        "beginning_nav":         round(beginning_nav, 4),
        "contribution":          round(contribution, 4),
        "disposition":           round(disposition, 4),
        "income":                round(income, 4),
        "cashflow_adjusted_nav": round(cf_adj_nav, 4),
        "income_reversal":       round(income_reversal, 4),
        "write_up_down":         round(write_up_down, 4),
        "ending_nav":            round(ending_nav, 4),
    }


def compute_deal_metrics(fund_id: str, deal_id: str, store: DataStore) -> dict[str, float]:
    """Investment-level metrics for one deal within a fund.
    Returns: total_invested, total_income, total_disposition,
             current_value (fund share), total_returned, moic, irr."""
    fund = store.funds.get(fund_id)
    deal = store.deals.get(deal_id)
    if not fund or not deal:
        return {}

    own          = store.get_ownership(fund_id, deal_id)
    own_pct      = own.ownership_pct if own else 1.0
    current_val  = round(deal.appraiser_nav * own_pct, 4)

    cfs              = store.get_cashflows(fund_id=fund_id, deal_id=deal_id)
    total_invested   = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
    total_disposition= sum(c.fund_amt      for c in cfs if c.cf_type == "disposition")
    total_income     = sum(c.fund_amt      for c in cfs if c.cf_type == "income")
    total_returned   = total_disposition + total_income

    if total_invested == 0:
        return {}

    moic = (total_returned + current_val) / total_invested

    terminal = date_type.fromisoformat(fund.reporting_date)
    irr_map: dict[date_type, float] = {}
    for c in cfs:
        d = date_type.fromisoformat(c.cash_date)
        irr_map[d] = irr_map.get(d, 0.0) + c.fund_amt
    irr_map[terminal] = irr_map.get(terminal, 0.0) + current_val
    irr = calculate_xirr(sorted(irr_map.items()))

    return {
        "total_invested":    round(total_invested, 4),
        "total_disposition": round(total_disposition, 4),
        "total_income":      round(total_income, 4),
        "total_returned":    round(total_returned, 4),
        "current_value":     current_val,
        "ownership_pct":     own_pct,
        "moic":              round(moic, 6),
        "irr":               round(irr, 6),
    }

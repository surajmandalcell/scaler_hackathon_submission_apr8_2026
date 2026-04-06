"""Tests for simplified FundLens calculations.
3 cashflow types: contribution | disposition | income
Fund-level USD, no FX.
"""
import pytest
from datetime import date
from fundlens.server.calculations import compute_nav_bridge, calculate_xirr, compute_metrics
from fundlens.models import Cashflow, Fund, Deal, Ownership
from fundlens.server.data_store import DataStore


def simple_store() -> DataStore:
    """Single-fund, single-deal store for deterministic testing."""
    s = DataStore()
    s.add_fund(Fund(
        fund_id="f1", fund_name="Test Fund",
        reporting_date="2024-12-31",
        beginning_nav=10.0, ending_nav=13.0,
        nav_period_start="2024-01-01",
    ))
    s.add_deal(Deal(deal_id="d1", property_name="Test Property",
                    sector="Office", location="Test City"))
    s.add_ownership(Ownership(deal_id="d1", fund_id="f1",
                              ownership_pct=1.0, entry_date="2022-01-01"))
    # Historical (pre-period) contributions
    s.add_cashflow(Cashflow(cashflow_id="c1", deal_id="d1", fund_id="f1",
                            cash_date="2022-01-01", cf_type="contribution", fund_amt=-8.0))
    s.add_cashflow(Cashflow(cashflow_id="c2", deal_id="d1", fund_id="f1",
                            cash_date="2023-06-01", cf_type="contribution", fund_amt=-2.0))
    # Period cashflows (2024)
    s.add_cashflow(Cashflow(cashflow_id="c3", deal_id="d1", fund_id="f1",
                            cash_date="2024-06-30", cf_type="disposition", fund_amt=2.0))
    s.add_cashflow(Cashflow(cashflow_id="c4", deal_id="d1", fund_id="f1",
                            cash_date="2024-12-31", cf_type="income", fund_amt=0.5))
    return s


# ── NAV Bridge ────────────────────────────────────────────────────────────

def test_bridge_ending_nav():
    s = simple_store()
    b = compute_nav_bridge("f1", s)
    assert abs(b["ending_nav"] - 13.0) < 1e-6

def test_bridge_balances():
    s = simple_store()
    b = compute_nav_bridge("f1", s)
    recomputed = b["cashflow_adjusted_nav"] + b["income_reversal"] + b["write_up_down"]
    assert abs(recomputed - b["ending_nav"]) < 1e-6

def test_bridge_cf_adjusted_nav():
    """CF Adj = Beg(10) + Contribution(0, all pre-period) - Disposition(2) + Income(0.5) = 8.5"""
    s = simple_store()
    b = compute_nav_bridge("f1", s)
    assert abs(b["cashflow_adjusted_nav"] - 8.5) < 1e-4

def test_bridge_write_up_down():
    """Write_Up = Ending(13) - (CF_Adj(8.5) + Income_Rev(-0.5)) = 13 - 8.0 = 5.0"""
    s = simple_store()
    b = compute_nav_bridge("f1", s)
    assert abs(b["write_up_down"] - 5.0) < 1e-4

def test_bridge_has_8_items():
    s = simple_store()
    b = compute_nav_bridge("f1", s)
    assert len(b) == 8

def test_bridge_contribution_is_zero_in_period():
    """No 2024 contributions → contribution=0 in bridge."""
    s = simple_store()
    b = compute_nav_bridge("f1", s)
    assert abs(b["contribution"] - 0.0) < 1e-9

def test_bridge_with_period_contribution():
    """Add a 2024 contribution and verify bridge updates."""
    s = simple_store()
    s.add_cashflow(Cashflow(cashflow_id="c5", deal_id="d1", fund_id="f1",
                            cash_date="2024-03-01", cf_type="contribution", fund_amt=-3.0))
    b = compute_nav_bridge("f1", s)
    assert abs(b["contribution"] - 3.0) < 1e-4    # shown as positive
    assert abs(b["cashflow_adjusted_nav"] - 11.5) < 1e-4  # 10 + 3 - 2 + 0.5


# ── XIRR ──────────────────────────────────────────────────────────────────

def test_xirr_10pct():
    """Invest $1, receive $1.10 in 1 year = 10% IRR."""
    cfs = [(date(2023, 1, 1), -1.0), (date(2024, 1, 1), 1.1)]
    assert abs(calculate_xirr(cfs) - 0.10) < 0.001

def test_xirr_empty():
    assert calculate_xirr([]) == 0.0


# ── Metrics ───────────────────────────────────────────────────────────────

def test_metrics_moic():
    """MOIC = (disposition(2) + income(0.5) + ending_nav(13)) / invested(10) = 1.55"""
    s = simple_store()
    m = compute_metrics("f1", s)
    assert abs(m["moic"] - 1.55) < 0.001

def test_metrics_irr_positive():
    s = simple_store()
    m = compute_metrics("f1", s)
    assert m["irr"] > 0

def test_metrics_has_only_moic_irr():
    s = simple_store()
    m = compute_metrics("f1", s)
    assert set(m.keys()) == {"moic", "irr"}

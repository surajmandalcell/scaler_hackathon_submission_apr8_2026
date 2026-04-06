"""
Seed data for 3 FundLens tasks (easy / medium / hard).

Cashflow types:
  contribution  — capital deployed  (fund_amt NEGATIVE)
  disposition   — proceeds received (fund_amt POSITIVE)
  income        — quarterly rental / operating income (fund_amt POSITIVE)

All amounts in USD millions.  NAV bridge period = FY 2024 (nav_period_start="2024-01-01").

Sector return profile (based on market observations):
  Data Center  — IRR 28-35%  / MOIC 2.5-4x  (supply-constrained, AI-driven demand)
  Industrial   — IRR 15-20%  / MOIC 1.8-2.5x (logistics boom)
  Residential  — IRR 12-18%  / MOIC 1.5-2.2x
  Office       — IRR 10-15%  / MOIC 1.3-1.8x (selective, tier-1 cities only)

Income convention:
  Every deal pays quarterly income (Q1-Q4 each calendar year active).
  2024 income is bridge-period cashflow; 2022-2023 income is ITD only.
"""
from __future__ import annotations
from typing import Dict, Any
from fundlens.models import Fund, Deal, Ownership, Cashflow
from fundlens.server.data_store import DataStore
from fundlens.server.calculations import compute_nav_bridge, compute_metrics


TASK_DESCRIPTIONS = {
    "easy": (
        "RE Alpha Fund I — Q4 2024 reporting.  3 properties, all 100% owned. "
        "TASK (Level 1): compute the 8-line NAV bridge only. "
        "No performance metrics required."
    ),
    "medium": (
        "RE Beta Fund II — Q4 2024 reporting.  5 properties, 100% owned. "
        "TASK (Level 2): compute the NAV bridge AND MOIC."
    ),
    "hard": (
        "Cross-fund view — RE Alpha, Beta, Gamma. "
        "Prestige Tower co-invested: Beta 40%, Gamma 35%. "
        "TASK (Level 3): compute the NAV bridge AND MOIC AND IRR for the primary fund (alpha)."
    ),
}


def _cf_id(fund_id: str, deal_id: str, date: str, cf_type: str) -> str:
    """Deterministic cashflow ID — collision-safe on re-seed."""
    return f"{fund_id}_{deal_id}_{date}_{cf_type[:3]}"


def _add_deal(store, deal_id, name, sector, location, appraiser_nav,
              fund_id, ownership_pct, entry_date, cashflows):
    """Helper: add deal + ownership + cashflows in one call."""
    store.add_deal(Deal(deal_id=deal_id, property_name=name,
                        sector=sector, location=location,
                        appraiser_nav=appraiser_nav))
    store.add_ownership(Ownership(deal_id=deal_id, fund_id=fund_id,
                                  ownership_pct=ownership_pct,
                                  entry_date=entry_date))
    for date, amt, cf_type in cashflows:
        store.add_cashflow(Cashflow(
            cashflow_id=_cf_id(fund_id, deal_id, date, cf_type),
            deal_id=deal_id, fund_id=fund_id,
            cash_date=date, cf_type=cf_type, fund_amt=amt,
        ))


# ══════════════════════════════════════════════════════════════════════════════
# EASY — RE Alpha Fund I   (3 deals, 100% owned, no FX, no debt)
# ending_nav = sum of appraiser_navs = 18.80 + 15.20 + 8.30 = 42.30
# ══════════════════════════════════════════════════════════════════════════════

def load_easy_task(store: DataStore) -> None:
    store.clear()

    store.add_fund(Fund(
        fund_id="alpha", fund_name="RE Alpha Fund I",
        reporting_date="2024-12-31",
        beginning_nav=38.50, ending_nav=42.30,
        nav_period_start="2024-01-01",
    ))

    # ── Deal 1: Embassy Office Park (Office, Bangalore) ───────────────────
    # Invested: 11.0M  |  Appraiser NAV: 18.80M  |  MOIC ~1.9x  |  IRR ~14%
    _add_deal(store, "embassy", "Embassy Office Park",
              "Office", "Bangalore, India",
              appraiser_nav=18.80,
              fund_id="alpha", ownership_pct=1.0, entry_date="2022-01-15",
              cashflows=[
                  # contributions
                  ("2022-01-15", -8.00, "contribution"),
                  ("2023-06-01", -3.00, "contribution"),
                  # historical income — quarterly 2022
                  ("2022-06-30",  0.12, "income"),
                  ("2022-09-30",  0.13, "income"),
                  ("2022-12-31",  0.14, "income"),
                  # historical income — quarterly 2023
                  ("2023-03-31",  0.16, "income"),
                  ("2023-06-30",  0.18, "income"),
                  ("2023-09-30",  0.20, "income"),
                  ("2023-12-31",  0.22, "income"),
                  # partial disposition 2024
                  ("2024-09-30",  2.50, "disposition"),
                  # 2024 quarterly income (bridge period)
                  ("2024-03-31",  0.24, "income"),
                  ("2024-06-30",  0.26, "income"),
                  ("2024-09-30",  0.28, "income"),
                  ("2024-12-31",  0.32, "income"),
              ])

    # ── Deal 2: Prestige Residences (Residential, Mumbai) ─────────────────
    # Invested: 8.0M  |  Appraiser NAV: 15.20M  |  MOIC ~2.1x  |  IRR ~16%
    _add_deal(store, "prestige", "Prestige Residences",
              "Residential", "Mumbai, India",
              appraiser_nav=15.20,
              fund_id="alpha", ownership_pct=1.0, entry_date="2021-07-01",
              cashflows=[
                  # contributions
                  ("2021-07-01", -6.00, "contribution"),
                  ("2022-11-01", -2.00, "contribution"),
                  # historical income — quarterly 2021 H2
                  ("2021-09-30",  0.09, "income"),
                  ("2021-12-31",  0.10, "income"),
                  # historical income — quarterly 2022
                  ("2022-03-31",  0.12, "income"),
                  ("2022-06-30",  0.13, "income"),
                  ("2022-09-30",  0.14, "income"),
                  ("2022-12-31",  0.15, "income"),
                  # historical income — quarterly 2023
                  ("2023-03-31",  0.17, "income"),
                  ("2023-06-30",  0.18, "income"),
                  ("2023-09-30",  0.20, "income"),
                  ("2023-12-31",  0.22, "income"),
                  # partial disposition 2024
                  ("2024-07-31",  1.80, "disposition"),
                  # 2024 quarterly income (bridge period)
                  ("2024-03-31",  0.22, "income"),
                  ("2024-06-30",  0.24, "income"),
                  ("2024-09-30",  0.26, "income"),
                  ("2024-12-31",  0.28, "income"),
              ])

    # ── Deal 3: Mahindra Logistics Hub (Industrial, Pune) ─────────────────
    # Invested: 4.0M  |  Appraiser NAV: 8.30M  |  MOIC ~2.3x  |  IRR ~18%
    _add_deal(store, "mahindra", "Mahindra Logistics Hub",
              "Industrial", "Pune, India",
              appraiser_nav=8.30,
              fund_id="alpha", ownership_pct=1.0, entry_date="2022-10-01",
              cashflows=[
                  # contribution
                  ("2022-10-01", -4.00, "contribution"),
                  # historical income — quarterly 2022 Q4
                  ("2022-12-31",  0.08, "income"),
                  # historical income — quarterly 2023
                  ("2023-03-31",  0.10, "income"),
                  ("2023-06-30",  0.11, "income"),
                  ("2023-09-30",  0.12, "income"),
                  ("2023-12-31",  0.13, "income"),
                  # partial disposition 2024
                  ("2024-11-30",  1.20, "disposition"),
                  # 2024 quarterly income (bridge period)
                  ("2024-03-31",  0.14, "income"),
                  ("2024-06-30",  0.15, "income"),
                  ("2024-09-30",  0.16, "income"),
                  ("2024-12-31",  0.18, "income"),
              ])


# ══════════════════════════════════════════════════════════════════════════════
# MEDIUM — RE Beta Fund II  (5 deals, 100% owned, with Data Center)
# ending_nav = 22.50 + 19.80 + 12.40 + 7.80 + 6.00 = 68.50
# ══════════════════════════════════════════════════════════════════════════════

def load_medium_task(store: DataStore) -> None:
    store.clear()

    store.add_fund(Fund(
        fund_id="beta", fund_name="RE Beta Fund II",
        reporting_date="2024-12-31",
        beginning_nav=62.00, ending_nav=68.50,
        nav_period_start="2024-01-01",
    ))

    # ── Deal 1: Prestige Tower (Office, Bangalore) ─────────────────────────
    # Invested: 14.0M  |  Appraiser NAV: 22.50M  |  MOIC ~1.8x  |  IRR ~13%
    _add_deal(store, "prestige_tower", "Prestige Tower",
              "Office", "Bangalore, India",
              appraiser_nav=22.50,
              fund_id="beta", ownership_pct=1.0, entry_date="2021-09-01",
              cashflows=[
                  ("2021-09-01", -10.00, "contribution"),
                  ("2023-03-01",  -4.00, "contribution"),
                  # 2021 Q4
                  ("2021-12-31",   0.20, "income"),
                  # 2022 quarterly
                  ("2022-03-31",   0.25, "income"),
                  ("2022-06-30",   0.28, "income"),
                  ("2022-09-30",   0.30, "income"),
                  ("2022-12-31",   0.32, "income"),
                  # 2023 quarterly
                  ("2023-03-31",   0.35, "income"),
                  ("2023-06-30",   0.38, "income"),
                  ("2023-09-30",   0.40, "income"),
                  ("2023-12-31",   0.42, "income"),
                  # 2024 disposition + quarterly income
                  ("2024-08-01",   4.50, "disposition"),
                  ("2024-03-31",   0.44, "income"),
                  ("2024-06-30",   0.46, "income"),
                  ("2024-09-30",   0.48, "income"),
                  ("2024-12-31",   0.52, "income"),
              ])

    # ── Deal 2: Navi Mumbai Data Centre (Data Center) ──────────────────────
    # Invested: 11.0M  |  Appraiser NAV: 19.80M  |  MOIC ~2.1x  |  IRR ~30%
    # Strong AI-driven demand; high yield + rapid appreciation
    _add_deal(store, "navi_dc", "Navi Mumbai Data Centre",
              "Data Center", "Navi Mumbai, India",
              appraiser_nav=19.80,
              fund_id="beta", ownership_pct=1.0, entry_date="2022-04-01",
              cashflows=[
                  ("2022-04-01",  -8.00, "contribution"),
                  ("2024-01-15",  -3.00, "contribution"),
                  # 2022 Q2-Q4 (higher yield for DC — ~6.5% p.a.)
                  ("2022-06-30",   0.18, "income"),
                  ("2022-09-30",   0.20, "income"),
                  ("2022-12-31",   0.22, "income"),
                  # 2023 quarterly
                  ("2023-03-31",   0.24, "income"),
                  ("2023-06-30",   0.26, "income"),
                  ("2023-09-30",   0.28, "income"),
                  ("2023-12-31",   0.30, "income"),
                  # 2024 partial exit + quarterly income
                  ("2024-07-01",   2.00, "disposition"),
                  ("2024-03-31",   0.32, "income"),
                  ("2024-06-30",   0.35, "income"),
                  ("2024-09-30",   0.38, "income"),
                  ("2024-12-31",   0.42, "income"),
              ])

    # ── Deal 3: DLF Cyber City Tower (Office, Gurugram) ───────────────────
    # Invested: 8.5M  |  Appraiser NAV: 12.40M  |  MOIC ~1.6x  |  IRR ~12%
    _add_deal(store, "dlf_cyber", "DLF Cyber City Tower",
              "Office", "Gurugram, India",
              appraiser_nav=12.40,
              fund_id="beta", ownership_pct=1.0, entry_date="2023-01-01",
              cashflows=[
                  ("2023-01-01",  -6.00, "contribution"),
                  ("2024-03-01",  -2.50, "contribution"),
                  # 2023 quarterly
                  ("2023-03-31",   0.15, "income"),
                  ("2023-06-30",   0.17, "income"),
                  ("2023-09-30",   0.18, "income"),
                  ("2023-12-31",   0.20, "income"),
                  # 2024 disposition + quarterly income
                  ("2024-10-01",   1.50, "disposition"),
                  ("2024-03-31",   0.22, "income"),
                  ("2024-06-30",   0.24, "income"),
                  ("2024-09-30",   0.26, "income"),
                  ("2024-12-31",   0.28, "income"),
              ])

    # ── Deal 4: Mumbai Rental Towers (Residential, Mumbai) ────────────────
    # Invested: 9.0M  |  Appraiser NAV: 7.80M  |  MOIC ~1.2x  |  IRR ~8%
    # Below-par — residential slowdown
    _add_deal(store, "mumbai_rental", "Mumbai Rental Towers",
              "Residential", "Mumbai, India",
              appraiser_nav=7.80,
              fund_id="beta", ownership_pct=1.0, entry_date="2022-07-01",
              cashflows=[
                  ("2022-07-01",  -7.00, "contribution"),
                  ("2023-11-01",  -2.00, "contribution"),
                  # 2022 Q3-Q4
                  ("2022-09-30",   0.14, "income"),
                  ("2022-12-31",   0.15, "income"),
                  # 2023 quarterly
                  ("2023-03-31",   0.16, "income"),
                  ("2023-06-30",   0.17, "income"),
                  ("2023-09-30",   0.18, "income"),
                  ("2023-12-31",   0.19, "income"),
                  # 2024 disposition + quarterly income
                  ("2024-09-01",   3.20, "disposition"),
                  ("2024-03-31",   0.20, "income"),
                  ("2024-06-30",   0.21, "income"),
                  ("2024-09-30",   0.22, "income"),
                  ("2024-12-31",   0.24, "income"),
              ])

    # ── Deal 5: Chennai Logistics Park (Industrial, Chennai) ──────────────
    # Invested: 5.0M  |  Appraiser NAV: 6.00M  |  MOIC ~1.7x  |  IRR ~16%
    _add_deal(store, "chennai_log", "Chennai Logistics Park",
              "Industrial", "Chennai, India",
              appraiser_nav=6.00,
              fund_id="beta", ownership_pct=1.0, entry_date="2023-05-01",
              cashflows=[
                  ("2023-05-01",  -5.00, "contribution"),
                  # 2023 Q2-Q4
                  ("2023-06-30",   0.10, "income"),
                  ("2023-09-30",   0.12, "income"),
                  ("2023-12-31",   0.14, "income"),
                  # 2024 disposition + quarterly income
                  ("2024-11-01",   2.00, "disposition"),
                  ("2024-03-31",   0.16, "income"),
                  ("2024-06-30",   0.17, "income"),
                  ("2024-09-30",   0.18, "income"),
                  ("2024-12-31",   0.20, "income"),
              ])


# ══════════════════════════════════════════════════════════════════════════════
# HARD — 3 funds: Alpha + Beta (40%) + Gamma (35%) on Prestige Tower
# Alpha ending_nav = 18.80 + 15.20 + 8.30 = 42.30
# Beta  ending_nav = 22.50*0.40 + 19.80 + 12.40 + 7.80 + 6.00 = 55.00 → use 55.00
# Gamma ending_nav = 22.50*0.35 + 16.20 + 9.40 = 33.58 → use 33.60
# ══════════════════════════════════════════════════════════════════════════════

def load_hard_task(store: DataStore) -> None:
    store.clear()

    # ── Alpha (same deals as easy) ────────────────────────────────────────
    store.add_fund(Fund(
        fund_id="alpha", fund_name="RE Alpha Fund I",
        reporting_date="2024-12-31",
        beginning_nav=38.50, ending_nav=42.30,
        nav_period_start="2024-01-01",
    ))
    _load_alpha_deals(store)

    # ── Beta (Prestige Tower at 40% + 4 own deals) ────────────────────────
    # Beta ending_nav = 0.40*22.50 + 19.80 + 12.40 + 7.80 + 6.00 = 55.00
    store.add_fund(Fund(
        fund_id="beta", fund_name="RE Beta Fund II",
        reporting_date="2024-12-31",
        beginning_nav=50.00, ending_nav=55.00,
        nav_period_start="2024-01-01",
    ))

    # Prestige Tower — Beta owns 40%
    store.add_deal(Deal(deal_id="prestige_tower", property_name="Prestige Tower",
                        sector="Office", location="Bangalore, India",
                        appraiser_nav=22.50))
    store.add_ownership(Ownership(deal_id="prestige_tower", fund_id="beta",
                                  ownership_pct=0.40, entry_date="2021-09-01"))
    for date, amt, t in [
        ("2021-09-01",  -4.00, "contribution"),   # 40% of 10.0
        ("2023-03-01",  -1.60, "contribution"),   # 40% of 4.0
        ("2021-12-31",   0.08, "income"),
        ("2022-03-31",   0.10, "income"),
        ("2022-06-30",   0.11, "income"),
        ("2022-09-30",   0.12, "income"),
        ("2022-12-31",   0.13, "income"),
        ("2023-03-31",   0.14, "income"),
        ("2023-06-30",   0.15, "income"),
        ("2023-09-30",   0.16, "income"),
        ("2023-12-31",   0.17, "income"),
        ("2024-08-01",   1.80, "disposition"),    # 40% of 4.5
        ("2024-03-31",   0.18, "income"),
        ("2024-06-30",   0.19, "income"),
        ("2024-09-30",   0.20, "income"),
        ("2024-12-31",   0.21, "income"),
    ]:
        store.add_cashflow(Cashflow(
            cashflow_id=_cf_id("beta", "prestige_tower", date, t),
            deal_id="prestige_tower", fund_id="beta",
            cash_date=date, cf_type=t, fund_amt=amt,
        ))

    # Beta own deals (full ownership)
    for deal_id, name, sector, loc, appraiser_nav, cfs in [
        ("navi_dc", "Navi Mumbai Data Centre", "Data Center", "Navi Mumbai, India", 19.80, [
            ("2022-04-01",  -8.00, "contribution"),
            ("2024-01-15",  -3.00, "contribution"),
            ("2022-06-30",   0.18, "income"),
            ("2022-09-30",   0.20, "income"),
            ("2022-12-31",   0.22, "income"),
            ("2023-03-31",   0.24, "income"),
            ("2023-06-30",   0.26, "income"),
            ("2023-09-30",   0.28, "income"),
            ("2023-12-31",   0.30, "income"),
            ("2024-07-01",   2.00, "disposition"),
            ("2024-03-31",   0.32, "income"),
            ("2024-06-30",   0.35, "income"),
            ("2024-09-30",   0.38, "income"),
            ("2024-12-31",   0.42, "income"),
        ]),
        ("dlf_cyber", "DLF Cyber City Tower", "Office", "Gurugram, India", 12.40, [
            ("2023-01-01",  -6.00, "contribution"),
            ("2024-03-01",  -2.50, "contribution"),
            ("2023-03-31",   0.15, "income"),
            ("2023-06-30",   0.17, "income"),
            ("2023-09-30",   0.18, "income"),
            ("2023-12-31",   0.20, "income"),
            ("2024-10-01",   1.50, "disposition"),
            ("2024-03-31",   0.22, "income"),
            ("2024-06-30",   0.24, "income"),
            ("2024-09-30",   0.26, "income"),
            ("2024-12-31",   0.28, "income"),
        ]),
        ("mumbai_rental", "Mumbai Rental Towers", "Residential", "Mumbai, India", 7.80, [
            ("2022-07-01",  -7.00, "contribution"),
            ("2023-11-01",  -2.00, "contribution"),
            ("2022-09-30",   0.14, "income"),
            ("2022-12-31",   0.15, "income"),
            ("2023-03-31",   0.16, "income"),
            ("2023-06-30",   0.17, "income"),
            ("2023-09-30",   0.18, "income"),
            ("2023-12-31",   0.19, "income"),
            ("2024-09-01",   3.20, "disposition"),
            ("2024-03-31",   0.20, "income"),
            ("2024-06-30",   0.21, "income"),
            ("2024-09-30",   0.22, "income"),
            ("2024-12-31",   0.24, "income"),
        ]),
        ("chennai_log", "Chennai Logistics Park", "Industrial", "Chennai, India", 6.00, [
            ("2023-05-01",  -5.00, "contribution"),
            ("2023-06-30",   0.10, "income"),
            ("2023-09-30",   0.12, "income"),
            ("2023-12-31",   0.14, "income"),
            ("2024-11-01",   2.00, "disposition"),
            ("2024-03-31",   0.16, "income"),
            ("2024-06-30",   0.17, "income"),
            ("2024-09-30",   0.18, "income"),
            ("2024-12-31",   0.20, "income"),
        ]),
    ]:
        _add_deal(store, deal_id, name, sector, loc,
                  appraiser_nav=appraiser_nav,
                  fund_id="beta", ownership_pct=1.0, entry_date=cfs[0][0],
                  cashflows=cfs)

    # ── Gamma (Prestige Tower at 35% + 2 own deals) ───────────────────────
    # Gamma ending_nav = 0.35*22.50 + 16.20 + 9.40 = 7.875 + 16.20 + 9.40 = 33.475
    store.add_fund(Fund(
        fund_id="gamma", fund_name="RE Gamma Fund III",
        reporting_date="2024-12-31",
        beginning_nav=30.00, ending_nav=33.475,
        nav_period_start="2024-01-01",
    ))
    store.add_ownership(Ownership(deal_id="prestige_tower", fund_id="gamma",
                                  ownership_pct=0.35, entry_date="2021-09-01"))
    for date, amt, t in [
        ("2021-09-01",  -3.50, "contribution"),   # 35% of 10.0
        ("2023-03-01",  -1.40, "contribution"),   # 35% of 4.0
        ("2021-12-31",   0.07, "income"),
        ("2022-03-31",   0.09, "income"),
        ("2022-06-30",   0.10, "income"),
        ("2022-09-30",   0.11, "income"),
        ("2022-12-31",   0.11, "income"),
        ("2023-03-31",   0.12, "income"),
        ("2023-06-30",   0.13, "income"),
        ("2023-09-30",   0.14, "income"),
        ("2023-12-31",   0.15, "income"),
        ("2024-08-01",   1.58, "disposition"),    # 35% of 4.5
        ("2024-03-31",   0.16, "income"),
        ("2024-06-30",   0.16, "income"),
        ("2024-09-30",   0.17, "income"),
        ("2024-12-31",   0.18, "income"),
    ]:
        store.add_cashflow(Cashflow(
            cashflow_id=_cf_id("gamma", "prestige_tower", date, t),
            deal_id="prestige_tower", fund_id="gamma",
            cash_date=date, cf_type=t, fund_amt=amt,
        ))

    # Gamma own deals — Data Center (star performer) + Logistics
    for deal_id, name, sector, loc, appraiser_nav, cfs in [
        # Hyderabad Data Hub — strong returns, AI colocation demand
        # Invested: 7.0M  |  Appraiser NAV: 16.20M  |  MOIC ~2.7x  |  IRR ~32%
        ("hyderabad_dc", "Hyderabad Data Hub", "Data Center", "Hyderabad, India", 16.20, [
            ("2022-06-01",  -5.00, "contribution"),
            ("2023-08-01",  -2.00, "contribution"),
            ("2022-09-30",   0.16, "income"),
            ("2022-12-31",   0.18, "income"),
            ("2023-03-31",   0.21, "income"),
            ("2023-06-30",   0.24, "income"),
            ("2023-09-30",   0.27, "income"),
            ("2023-12-31",   0.30, "income"),
            ("2024-07-01",   2.40, "disposition"),
            ("2024-03-31",   0.34, "income"),
            ("2024-06-30",   0.38, "income"),
            ("2024-09-30",   0.42, "income"),
            ("2024-12-31",   0.46, "income"),
        ]),
        # Pune Mega Logistics — industrial, solid mid-teens IRR
        # Invested: 6.0M  |  Appraiser NAV: 9.40M  |  MOIC ~2.0x  |  IRR ~17%
        ("pune_logistics", "Pune Mega Logistics", "Industrial", "Pune, India", 9.40, [
            ("2023-02-01",  -6.00, "contribution"),
            ("2023-03-31",   0.12, "income"),
            ("2023-06-30",   0.14, "income"),
            ("2023-09-30",   0.16, "income"),
            ("2023-12-31",   0.18, "income"),
            ("2024-10-01",   2.80, "disposition"),
            ("2024-03-31",   0.20, "income"),
            ("2024-06-30",   0.22, "income"),
            ("2024-09-30",   0.24, "income"),
            ("2024-12-31",   0.26, "income"),
        ]),
    ]:
        _add_deal(store, deal_id, name, sector, loc,
                  appraiser_nav=appraiser_nav,
                  fund_id="gamma", ownership_pct=1.0, entry_date=cfs[0][0],
                  cashflows=cfs)


def _load_alpha_deals(store: DataStore) -> None:
    """Reusable alpha deals loader (used by hard task)."""
    for deal_id, name, sector, loc, appraiser_nav, cfs in [
        ("embassy", "Embassy Office Park", "Office", "Bangalore, India", 18.80, [
            ("2022-01-15", -8.00, "contribution"),
            ("2023-06-01", -3.00, "contribution"),
            ("2022-06-30",  0.12, "income"),
            ("2022-09-30",  0.13, "income"),
            ("2022-12-31",  0.14, "income"),
            ("2023-03-31",  0.16, "income"),
            ("2023-06-30",  0.18, "income"),
            ("2023-09-30",  0.20, "income"),
            ("2023-12-31",  0.22, "income"),
            ("2024-09-30",  2.50, "disposition"),
            ("2024-03-31",  0.24, "income"),
            ("2024-06-30",  0.26, "income"),
            ("2024-09-30",  0.28, "income"),
            ("2024-12-31",  0.32, "income"),
        ]),
        ("prestige", "Prestige Residences", "Residential", "Mumbai, India", 15.20, [
            ("2021-07-01", -6.00, "contribution"),
            ("2022-11-01", -2.00, "contribution"),
            ("2021-09-30",  0.09, "income"),
            ("2021-12-31",  0.10, "income"),
            ("2022-03-31",  0.12, "income"),
            ("2022-06-30",  0.13, "income"),
            ("2022-09-30",  0.14, "income"),
            ("2022-12-31",  0.15, "income"),
            ("2023-03-31",  0.17, "income"),
            ("2023-06-30",  0.18, "income"),
            ("2023-09-30",  0.20, "income"),
            ("2023-12-31",  0.22, "income"),
            ("2024-07-31",  1.80, "disposition"),
            ("2024-03-31",  0.22, "income"),
            ("2024-06-30",  0.24, "income"),
            ("2024-09-30",  0.26, "income"),
            ("2024-12-31",  0.28, "income"),
        ]),
        ("mahindra", "Mahindra Logistics Hub", "Industrial", "Pune, India", 8.30, [
            ("2022-10-01", -4.00, "contribution"),
            ("2022-12-31",  0.08, "income"),
            ("2023-03-31",  0.10, "income"),
            ("2023-06-30",  0.11, "income"),
            ("2023-09-30",  0.12, "income"),
            ("2023-12-31",  0.13, "income"),
            ("2024-11-30",  1.20, "disposition"),
            ("2024-03-31",  0.14, "income"),
            ("2024-06-30",  0.15, "income"),
            ("2024-09-30",  0.16, "income"),
            ("2024-12-31",  0.18, "income"),
        ]),
    ]:
        _add_deal(store, deal_id, name, sector, loc,
                  appraiser_nav=appraiser_nav,
                  fund_id="alpha", ownership_pct=1.0, entry_date=cfs[0][0],
                  cashflows=cfs)


# ── Ground-truth answer generator ────────────────────────────────────────────

def get_correct_answers(store: DataStore) -> Dict[str, Any]:
    answers: Dict[str, Any] = {}
    for fund_id in store.funds:
        answers[f"nav_bridge_{fund_id}"] = compute_nav_bridge(fund_id, store)
        answers[f"metrics_{fund_id}"]    = compute_metrics(fund_id, store)
    return answers

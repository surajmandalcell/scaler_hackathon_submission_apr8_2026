"""Tests for seed data integrity -- all 3 difficulty levels."""
import pytest
from fundlens.server.data_store import DataStore
from fundlens.server.seed_data import (
    load_easy_task, load_medium_task, load_hard_task,
    get_correct_answers, TASK_DESCRIPTIONS,
)
from fundlens.server.calculations import compute_nav_bridge


def test_easy_loads():
    s = DataStore()
    load_easy_task(s)
    assert len(s.funds) == 1
    assert len(s.deals) >= 3


def test_medium_loads():
    s = DataStore()
    load_medium_task(s)
    assert len(s.funds) == 1
    assert len(s.deals) >= 5


def test_hard_loads():
    s = DataStore()
    load_hard_task(s)
    assert len(s.funds) >= 2
    assert len(s.deals) >= 5


def test_easy_bridge_balances():
    s = DataStore()
    load_easy_task(s)
    for fid in s.funds:
        b = compute_nav_bridge(fid, s)
        recomputed = b["cashflow_adjusted_nav"] + b["income_reversal"] + b["write_up_down"]
        assert abs(recomputed - b["ending_nav"]) < 0.01, f"Bridge imbalance for {fid}"


def test_medium_bridge_balances():
    s = DataStore()
    load_medium_task(s)
    for fid in s.funds:
        b = compute_nav_bridge(fid, s)
        recomputed = b["cashflow_adjusted_nav"] + b["income_reversal"] + b["write_up_down"]
        assert abs(recomputed - b["ending_nav"]) < 0.01, f"Bridge imbalance for {fid}"


def test_hard_bridge_balances():
    s = DataStore()
    load_hard_task(s)
    for fid in s.funds:
        b = compute_nav_bridge(fid, s)
        recomputed = b["cashflow_adjusted_nav"] + b["income_reversal"] + b["write_up_down"]
        assert abs(recomputed - b["ending_nav"]) < 0.01, f"Bridge imbalance for {fid}"


def test_correct_answers_exist():
    for loader in [load_easy_task, load_medium_task, load_hard_task]:
        s = DataStore()
        loader(s)
        answers = get_correct_answers(s)
        assert len(answers) >= 1


def test_task_descriptions_exist():
    for key in ["easy", "medium", "hard"]:
        assert key in TASK_DESCRIPTIONS
        assert len(TASK_DESCRIPTIONS[key]) > 10


def test_all_deals_have_ownership():
    for loader in [load_easy_task, load_medium_task, load_hard_task]:
        s = DataStore()
        loader(s)
        for fid in s.funds:
            for deal in s.get_deals_for_fund(fid):
                own = s.get_ownership(fid, deal.deal_id)
                assert own is not None, f"Missing ownership for {fid}/{deal.deal_id}"
                assert 0.0 < own.ownership_pct <= 1.0


def test_all_deals_have_cashflows():
    for loader in [load_easy_task, load_medium_task, load_hard_task]:
        s = DataStore()
        loader(s)
        for fid in s.funds:
            for deal in s.get_deals_for_fund(fid):
                cfs = s.get_cashflows(fund_id=fid, deal_id=deal.deal_id)
                assert len(cfs) >= 1, f"No cashflows for {fid}/{deal.deal_id}"

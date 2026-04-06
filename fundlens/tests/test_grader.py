"""Tests for grader — verifies scoring logic and tolerance enforcement."""
import pytest
from fundlens.server.grader import (
    grade_nav_bridge, grade_metrics, grade_full_submission,
    TOL_AMOUNT, TOL_MULTIPLE, TOL_IRR,
)


# ── Fixtures: correct answers (match grader's exact 8-item + 2-metric spec) ──

CORRECT_BRIDGE = {
    "beginning_nav":         10.00,
    "contribution":           5.00,   # positive (capital deployed, sign-flipped from fund_amt)
    "disposition":            2.00,   # positive (proceeds received)
    "income":                 0.50,   # positive (rental / operating income)
    "cashflow_adjusted_nav": 13.50,   # = 10.00 + 5.00 − 2.00 + 0.50
    "income_reversal":       -0.50,   # = −income
    "write_up_down":          1.00,   # plug = ending_nav − (cf_adj_nav + income_reversal)
    "ending_nav":            14.00,   # = 13.50 + (−0.50) + 1.00
}

CORRECT_METRICS = {
    "moic": 1.50,    # (dispositions + income + ending_nav) / contributions
    "irr":  0.15,    # XIRR on all dated cashflows + terminal ending NAV
}


# ── grade_nav_bridge ───────────────────────────────────────────────────────

def test_grade_nav_bridge_perfect():
    result = grade_nav_bridge(CORRECT_BRIDGE, CORRECT_BRIDGE)
    assert result["score"] == result["total"], "Perfect submission should score 100%"
    assert result["reward"] == pytest.approx(1.0)


def test_grade_nav_bridge_all_wrong():
    garbage = {k: v + 999.0 for k, v in CORRECT_BRIDGE.items()}
    result = grade_nav_bridge(garbage, CORRECT_BRIDGE)
    assert result["score"] == 0
    assert result["reward"] == pytest.approx(0.0)


def test_grade_nav_bridge_within_tolerance():
    """Values within ±TOL_AMOUNT should still score full marks."""
    close = dict(CORRECT_BRIDGE)
    close["write_up_down"] = CORRECT_BRIDGE["write_up_down"] + TOL_AMOUNT * 0.9
    result = grade_nav_bridge(close, CORRECT_BRIDGE)
    assert result["reward"] == pytest.approx(1.0)


def test_grade_nav_bridge_just_outside_tolerance():
    """Values outside ±TOL_AMOUNT should lose that item's score."""
    off = dict(CORRECT_BRIDGE)
    off["ending_nav"] = CORRECT_BRIDGE["ending_nav"] + TOL_AMOUNT * 1.1
    result_off = grade_nav_bridge(off, CORRECT_BRIDGE)
    result_ok  = grade_nav_bridge(CORRECT_BRIDGE, CORRECT_BRIDGE)
    assert result_off["score"] < result_ok["score"]


def test_grade_nav_bridge_missing_keys():
    """Partial submission (missing keys) should score 0 for missing items."""
    partial = {"beginning_nav": CORRECT_BRIDGE["beginning_nav"], "ending_nav": CORRECT_BRIDGE["ending_nav"]}
    result = grade_nav_bridge(partial, CORRECT_BRIDGE)
    assert result["reward"] < 1.0
    assert result["score"] < result["total"]


# ── grade_metrics ──────────────────────────────────────────────────────────

def test_grade_metrics_perfect():
    result = grade_metrics(CORRECT_METRICS, CORRECT_METRICS, task_id="hard")
    assert result["reward"] == pytest.approx(1.0)


def test_grade_metrics_all_wrong():
    garbage = {k: v + 99.0 for k, v in CORRECT_METRICS.items()}
    result = grade_metrics(garbage, CORRECT_METRICS, task_id="hard")
    assert result["reward"] == pytest.approx(0.0)


def test_grade_metrics_irr_within_tolerance():
    close = dict(CORRECT_METRICS)
    close["irr"] = CORRECT_METRICS["irr"] + TOL_IRR * 0.9
    result = grade_metrics(close, CORRECT_METRICS, task_id="hard")
    assert result["reward"] == pytest.approx(1.0)


def test_grade_metrics_irr_outside_tolerance():
    off = dict(CORRECT_METRICS)
    off["irr"] = CORRECT_METRICS["irr"] + TOL_IRR * 1.1
    result_off = grade_metrics(off, CORRECT_METRICS, task_id="hard")
    result_ok  = grade_metrics(CORRECT_METRICS, CORRECT_METRICS, task_id="hard")
    assert result_off["score"] < result_ok["score"]


def test_grade_metrics_moic_tolerance():
    close = dict(CORRECT_METRICS)
    close["moic"] = CORRECT_METRICS["moic"] + TOL_MULTIPLE * 0.9
    assert grade_metrics(close, CORRECT_METRICS, task_id="hard")["reward"] == pytest.approx(1.0)

    off = dict(CORRECT_METRICS)
    off["moic"] = CORRECT_METRICS["moic"] + TOL_MULTIPLE * 1.1
    assert grade_metrics(off, CORRECT_METRICS, task_id="hard")["reward"] < 1.0


# ── grade_full_submission ──────────────────────────────────────────────────

def test_grade_full_submission_perfect():
    result = grade_full_submission(
        nav_bridge=CORRECT_BRIDGE,
        metrics=CORRECT_METRICS,
        correct_bridge=CORRECT_BRIDGE,
        correct_metrics=CORRECT_METRICS,
        task_id="hard",
    )
    assert result["reward"] == pytest.approx(1.0)
    assert result["bridge_reward"] == pytest.approx(1.0)
    assert result["metrics_reward"] == pytest.approx(1.0)


def test_grade_full_submission_partial():
    """If bridge is perfect but metrics are wrong, reward should be < 1."""
    garbage_metrics = {k: v + 99.0 for k, v in CORRECT_METRICS.items()}
    result = grade_full_submission(
        nav_bridge=CORRECT_BRIDGE,
        metrics=garbage_metrics,
        correct_bridge=CORRECT_BRIDGE,
        correct_metrics=CORRECT_METRICS,
        task_id="hard",
    )
    assert 0.0 < result["reward"] < 1.0
    assert result["bridge_reward"] == pytest.approx(1.0)
    assert result["metrics_reward"] == pytest.approx(0.0)


def test_grade_full_submission_none_metrics():
    """Submitting None for metrics should be treated as 0 metrics score."""
    result = grade_full_submission(
        nav_bridge=CORRECT_BRIDGE,
        metrics=None,
        correct_bridge=CORRECT_BRIDGE,
        correct_metrics=CORRECT_METRICS,
        task_id="hard",
    )
    assert result["metrics_reward"] == pytest.approx(0.0)
    assert result["bridge_reward"] == pytest.approx(1.0)
    assert 0.0 < result["reward"] < 1.0


def test_grade_full_submission_none_bridge():
    result = grade_full_submission(
        nav_bridge=None,
        metrics=CORRECT_METRICS,
        correct_bridge=CORRECT_BRIDGE,
        correct_metrics=CORRECT_METRICS,
        task_id="hard",
    )
    assert result["bridge_reward"] == pytest.approx(0.0)
    assert result["metrics_reward"] == pytest.approx(1.0)
    assert 0.0 < result["reward"] < 1.0


def test_grade_full_submission_both_none():
    result = grade_full_submission(
        nav_bridge=None, metrics=None,
        correct_bridge=CORRECT_BRIDGE,
        correct_metrics=CORRECT_METRICS,
        task_id="hard",
    )
    assert result["reward"] == pytest.approx(0.0)


def test_grader_never_returns_constant():
    """Score must vary with input — graders must not return constants."""
    r_perfect = grade_full_submission(
        CORRECT_BRIDGE, CORRECT_METRICS,
        CORRECT_BRIDGE, CORRECT_METRICS,
        task_id="hard",
    )
    r_garbage = grade_full_submission(
        {k: 0.0 for k in CORRECT_BRIDGE},
        {k: 0.0 for k in CORRECT_METRICS},
        CORRECT_BRIDGE, CORRECT_METRICS,
        task_id="hard",
    )
    assert r_perfect["reward"] != r_garbage["reward"]

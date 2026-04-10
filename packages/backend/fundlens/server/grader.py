"""Grader for FundLens submissions. Returns reward in (0, 1) exclusive.

Difficulty levels define WHAT is graded:
  easy   — NAV bridge only (8 items, 100%)
  medium — NAV bridge (60%) + MOIC (40%)
  hard   — NAV bridge (50%) + MOIC + IRR (50%)
"""
from __future__ import annotations

# ── Tolerances ────────────────────────────────────────────────────────────
TOL_AMOUNT   = 0.50   # ±$0.50M for NAV bridge line items
TOL_MULTIPLE = 0.02   # ±0.02x for MOIC
TOL_IRR      = 0.01   # ±1% absolute for IRR

# Evaluator requires task scores strictly in (0, 1) — never exactly 0.0 or 1.0.
REWARD_EPS = 0.01

# ── NAV Bridge (8 items) ──────────────────────────────────────────────────
_BRIDGE_ITEMS = [
    "beginning_nav",
    "contribution",
    "disposition",
    "income",
    "cashflow_adjusted_nav",
    "income_reversal",
    "write_up_down",
    "ending_nav",
]

# ── Metrics per level ─────────────────────────────────────────────────────
_MEDIUM_METRICS: dict[str, float] = {"moic": TOL_MULTIPLE}
_HARD_METRICS:   dict[str, float] = {"moic": TOL_MULTIPLE, "irr": TOL_IRR}

# ── Weights per level ─────────────────────────────────────────────────────
_TASK_WEIGHTS = {
    "easy":   (1.00, 0.00),
    "medium": (0.60, 0.40),
    "hard":   (0.50, 0.50),
}


def grade_nav_bridge(
    submitted: dict[str, float] | None,
    correct: dict[str, float],
) -> dict:
    if not submitted:
        return {"score": 0, "total": len(_BRIDGE_ITEMS), "reward": 0.0, "details": {}}
    details: dict[str, bool] = {}
    for key in _BRIDGE_ITEMS:
        sub = submitted.get(key)
        details[key] = sub is not None and abs(float(sub) - correct.get(key, 0.0)) <= TOL_AMOUNT
    score = sum(details.values())
    total = len(_BRIDGE_ITEMS)
    return {"score": score, "total": total, "reward": score / total, "details": details}


def grade_metrics(
    submitted: dict[str, float] | None,
    correct: dict[str, float],
    task_id: str = "hard",
) -> dict:
    tolerances = _HARD_METRICS if task_id == "hard" else _MEDIUM_METRICS
    if not submitted:
        return {"score": 0, "total": len(tolerances), "reward": 0.0, "details": {}}
    details: dict[str, bool] = {}
    for key, tol in tolerances.items():
        sub = submitted.get(key)
        details[key] = sub is not None and abs(float(sub) - correct.get(key, 0.0)) <= tol
    score = sum(details.values())
    total = len(tolerances)
    return {"score": score, "total": total, "reward": score / total if total else 0.0, "details": details}


def grade_full_submission(
    nav_bridge: dict[str, float] | None,
    metrics: dict[str, float] | None,
    correct_bridge: dict[str, float],
    correct_metrics: dict[str, float],
    task_id: str = "easy",
) -> dict:
    bridge_w, metrics_w = _TASK_WEIGHTS.get(task_id, (0.60, 0.40))
    bridge_r_obj = grade_nav_bridge(nav_bridge, correct_bridge)
    bridge_r: float = bridge_r_obj["reward"]  # type: ignore[assignment]

    if task_id == "easy":
        overall = bridge_r
        metrics_r_obj = {"score": 0, "total": 0, "reward": 0.0, "details": {}}
        metrics_score_str = "N/A (Level 1: bridge only)"
    else:
        metrics_r_obj = grade_metrics(metrics, correct_metrics, task_id)
        metrics_reward: float = metrics_r_obj["reward"]  # type: ignore[assignment]
        overall = bridge_w * bridge_r + metrics_w * metrics_reward
        metrics_score_str = f"{metrics_r_obj['score']}/{metrics_r_obj['total']}"

    overall = max(REWARD_EPS, min(1.0 - REWARD_EPS, overall))

    m_reward: float = metrics_r_obj["reward"]  # type: ignore[assignment]
    return {
        "reward":          round(overall, 6),
        "task_id":         task_id,
        "bridge_reward":   round(bridge_r, 6),
        "metrics_reward":  round(m_reward, 6),
        "bridge_details":  bridge_r_obj["details"],
        "metrics_details": metrics_r_obj["details"],
        "bridge_score":    f"{bridge_r_obj['score']}/{bridge_r_obj['total']}",
        "metrics_score":   metrics_score_str,
    }

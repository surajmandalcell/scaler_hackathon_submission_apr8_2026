"""Tests for MCP environment tools and lifecycle."""
import pytest
from openenv.core.env_server import CallToolAction
from fundlens.server.environment import FundLensEnvironment


def make_env():
    return FundLensEnvironment()


def tool_data(obs):
    """Extract dict data from a CallToolObservation."""
    assert obs.result is not None, f"Tool error: {obs.error}"
    return obs.result.data


# ── Lifecycle ──────────────────────────────────────────────────────────────

def test_reset_easy_returns_observation():
    env = make_env()
    obs = env.reset(task_id="easy")
    assert obs.task_id == "easy"
    assert obs.difficulty == "easy"
    assert "alpha" in obs.available_funds
    assert obs.portfolio_nav_usd > 0


def test_reset_medium_returns_observation():
    env = make_env()
    obs = env.reset(task_id="medium")
    assert obs.task_id == "medium"
    assert "beta" in obs.available_funds


def test_reset_hard_has_3_funds():
    env = make_env()
    obs = env.reset(task_id="hard")
    assert len(obs.available_funds) >= 3
    assert "alpha" in obs.available_funds
    assert "beta" in obs.available_funds
    assert "gamma" in obs.available_funds


def test_state_after_reset():
    env = make_env()
    env.reset(task_id="easy")
    assert env.state.task_id == "easy"
    assert not env.state.is_done


# ── Tool: get_available_filters ────────────────────────────────────────────

def test_get_available_filters():
    env = make_env()
    env.reset(task_id="easy")
    obs = env.step(CallToolAction(tool_name="get_available_filters", arguments={}))
    data = tool_data(obs)
    assert "fund_ids" in data
    assert "deal_ids" in data
    assert "alpha" in data["fund_ids"]


# ── Tool: get_nav_bridge ───────────────────────────────────────────────────

def test_get_nav_bridge():
    env = make_env()
    env.reset(task_id="easy")
    obs = env.step(CallToolAction(
        tool_name="get_nav_bridge",
        arguments={"fund_id": "alpha"},
    ))
    bridge = tool_data(obs)
    assert "beginning_nav" in bridge
    assert "ending_nav" in bridge
    assert "write_up_down" in bridge
    assert abs(bridge["ending_nav"] - 42.30) < 0.05


# ── Tool: get_portfolio_summary ────────────────────────────────────────────

def test_get_portfolio_summary():
    env = make_env()
    env.reset(task_id="easy")
    obs = env.step(CallToolAction(
        tool_name="get_portfolio_summary",
        arguments={},
    ))
    data = tool_data(obs)
    assert "alpha" in data
    assert "moic" in data["alpha"]
    assert data["alpha"]["moic"] > 1.0


# ── Tool: get_irr ──────────────────────────────────────────────────────────

def test_get_irr_both():
    env = make_env()
    env.reset(task_id="easy")
    obs = env.step(CallToolAction(
        tool_name="get_irr",
        arguments={"fund_id": "alpha"},
    ))
    data = tool_data(obs)
    assert "irr" in data
    assert isinstance(data["irr"], float)


# ── Tool: submit_report ────────────────────────────────────────────────────

def test_submit_report_with_correct_answers_scores_high():
    env = make_env()
    env.reset(task_id="easy")

    bridge_obs = env.step(CallToolAction(
        tool_name="get_nav_bridge", arguments={"fund_id": "alpha"},
    ))
    metrics_obs = env.step(CallToolAction(
        tool_name="get_irr", arguments={"fund_id": "alpha"},
    ))
    summary_obs = env.step(CallToolAction(
        tool_name="get_portfolio_summary", arguments={},
    ))
    summary = tool_data(summary_obs)["alpha"]
    metrics = {**tool_data(metrics_obs), **{k: summary[k] for k in ("moic",) if k in summary}}

    submit_obs = env.step(CallToolAction(
        tool_name="submit_report",
        arguments={
            "nav_bridge": tool_data(bridge_obs),
            "metrics": metrics,
        },
    ))
    result = tool_data(submit_obs)
    assert "reward" in result
    assert result["reward"] >= 0.9   # correct answers should score near 1.0
    assert env.state.is_done


def test_submit_report_garbage_scores_low():
    env = make_env()
    env.reset(task_id="easy")
    obs = env.step(CallToolAction(
        tool_name="submit_report",
        arguments={
            "nav_bridge": {k: 0.0 for k in [
                "beginning_nav", "contribution", "roc", "gl_on_investment",
                "gl_of_fx", "current_income", "cashflow_adjusted_nav",
                "income_reversal", "debt_mtm", "write_up_down", "ending_nav",
            ]},
            "metrics": {"moic": 0.0, "dpi": 0.0, "rvpi": 0.0, "tvpi": 0.0,
                        "irr_post_fx": 0.0, "irr_pre_fx": 0.0, "fx_attribution": 0.0},
        },
    ))
    result = tool_data(obs)
    assert result["reward"] < 0.2


def test_submit_ends_episode():
    env = make_env()
    env.reset(task_id="easy")
    assert not env.state.is_done
    env.step(CallToolAction(
        tool_name="submit_report",
        arguments={"nav_bridge": {}, "metrics": {}},
    ))
    assert env.state.is_done

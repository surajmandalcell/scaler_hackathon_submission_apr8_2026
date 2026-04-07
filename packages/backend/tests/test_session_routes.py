"""Tests for /api/session/* playground routes."""
from __future__ import annotations

from fastapi.testclient import TestClient

from fundlens.server.app import app

client = TestClient(app)


def _reset(task_id: str = "easy") -> dict:
    resp = client.post("/api/session/reset", json={"task_id": task_id})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_reset_loads_task():
    data = _reset("easy")
    state = data["state"]
    assert state["task_id"] == "easy"
    assert state["is_done"] is False
    assert len(state["funds_loaded"]) >= 1
    obs = data["observation"]
    assert obs["task_id"] == "easy"
    assert "available_funds" in obs


def test_tools_catalogue_shape():
    # Warm up the env so tool registry is ready
    _reset("easy")
    resp = client.get("/api/session/tools")
    assert resp.status_code == 200
    tools = resp.json()["tools"]
    assert isinstance(tools, list)
    assert len(tools) >= 10  # env.py declares 15 tools

    names = {t["name"] for t in tools}
    # Spot-check a few critical tools exist in the catalogue
    assert "get_nav_bridge" in names
    assert "get_portfolio_summary" in names
    assert "submit_report" in names
    assert "get_available_filters" in names

    # Every entry must have the dynamic-form-ready shape
    for t in tools:
        assert "name" in t and isinstance(t["name"], str)
        assert "description" in t
        assert "parameters" in t
        assert t["parameters"].get("type") == "object"
        assert "properties" in t["parameters"]


def test_step_get_nav_bridge():
    reset_data = _reset("easy")
    primary_fund = reset_data["observation"]["available_funds"][0]

    resp = client.post(
        "/api/session/step",
        json={"tool_name": "get_nav_bridge", "arguments": {"fund_id": primary_fund}},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tool_name"] == "get_nav_bridge"
    bridge = body["result"]
    # 8 line items
    assert len(bridge) == 8
    assert "beginning_nav" in bridge
    assert "ending_nav" in bridge
    assert "write_up_down" in bridge


def test_step_statefulness_across_requests():
    """Reset once, then fire multiple /step calls -- they must all see the
    same loaded store. This is what fails if demo_env isn't shared properly.
    """
    _reset("hard")
    # First call: list filters
    r1 = client.post(
        "/api/session/step",
        json={"tool_name": "get_available_filters", "arguments": {}},
    )
    filters = r1.json()["result"]
    assert len(filters["fund_ids"]) >= 2

    # Second call: NAV bridge on a fund pulled from the filter result
    primary = filters["fund_ids"][0]
    r2 = client.post(
        "/api/session/step",
        json={"tool_name": "get_nav_bridge", "arguments": {"fund_id": primary}},
    )
    bridge = r2.json()["result"]
    assert "error" not in bridge, f"cross-request state lost: {bridge}"
    assert bridge["ending_nav"] > 0


def test_submit_roundtrip_easy():
    """End-to-end: reset easy, get bridge, submit, assert reward > 0."""
    reset_data = _reset("easy")
    primary = reset_data["observation"]["available_funds"][0]

    bridge_resp = client.post(
        "/api/session/step",
        json={"tool_name": "get_nav_bridge", "arguments": {"fund_id": primary}},
    )
    bridge = bridge_resp.json()["result"]

    submit_resp = client.post(
        "/api/session/submit",
        json={"nav_bridge": bridge},
    )
    assert submit_resp.status_code == 200
    grading = submit_resp.json()["grading"]
    assert "reward" in grading
    assert grading["reward"] >= 0.9, f"pass-through bridge should grade near 1.0: {grading}"


def test_state_before_reset_is_empty_or_prior_task():
    """The /state endpoint should always respond even if the user hasn't
    reset yet this session; the shape is stable."""
    resp = client.get("/api/session/state")
    assert resp.status_code == 200
    state = resp.json()
    assert "task_id" in state
    assert "funds_loaded" in state
    assert "deals_loaded" in state
    assert isinstance(state["funds_loaded"], list)

"""Tests for REST API endpoints."""
import pytest
from fastapi.testclient import TestClient
from fundlens.server.app import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    # OpenEnv's create_app installs its own /health that returns {"status": "healthy"}
    assert resp.json()["status"] in ("ok", "healthy")


def test_load_scenario_easy():
    resp = client.post("/api/load-scenario?task_id=easy")
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "easy"
    assert data["fund_count"] >= 1


def test_load_scenario_medium():
    resp = client.post("/api/load-scenario?task_id=medium")
    assert resp.status_code == 200
    assert resp.json()["fund_count"] >= 1


def test_load_scenario_hard():
    resp = client.post("/api/load-scenario?task_id=hard")
    assert resp.status_code == 200
    assert resp.json()["fund_count"] >= 2


def test_portfolio_after_load():
    client.post("/api/load-scenario?task_id=easy")
    resp = client.get("/api/portfolio")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    for fid, fund in data.items():
        assert "fund_name" in fund
        assert "beginning_nav" in fund
        assert "ending_nav" in fund
        assert "moic" in fund


def test_bridge_after_load():
    client.post("/api/load-scenario?task_id=easy")
    resp = client.get("/api/portfolio")
    fund_id = list(resp.json().keys())[0]
    resp = client.get(f"/api/bridge/{fund_id}")
    assert resp.status_code == 200
    bridge = resp.json()
    assert "beginning_nav" in bridge
    assert "ending_nav" in bridge
    assert "write_up_down" in bridge
    assert len(bridge) == 8


def test_bridge_balances():
    client.post("/api/load-scenario?task_id=easy")
    resp = client.get("/api/portfolio")
    fund_id = list(resp.json().keys())[0]
    b = client.get(f"/api/bridge/{fund_id}").json()
    recomputed = b["cashflow_adjusted_nav"] + b["income_reversal"] + b["write_up_down"]
    assert abs(recomputed - b["ending_nav"]) < 0.01


def test_deals_after_load():
    client.post("/api/load-scenario?task_id=easy")
    resp = client.get("/api/portfolio")
    fund_id = list(resp.json().keys())[0]
    resp = client.get(f"/api/deals/{fund_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["deals"]) >= 1
    deal = data["deals"][0]
    assert "property_name" in deal
    assert "sector" in deal
    assert "ownership_pct" in deal


def test_cashflows_after_load():
    client.post("/api/load-scenario?task_id=easy")
    resp = client.get("/api/portfolio")
    fund_id = list(resp.json().keys())[0]
    resp = client.get(f"/api/cashflows/{fund_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_contribution"] > 0
    assert len(data["records"]) >= 1


def test_sectors_after_load():
    client.post("/api/load-scenario?task_id=easy")
    resp = client.get("/api/sectors")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    for sector, info in data.items():
        assert "total_invested" in info
        assert "deal_count" in info


def test_bridge_not_found():
    resp = client.get("/api/bridge/nonexistent")
    assert resp.status_code == 200
    assert "error" in resp.json()


def test_deals_not_found():
    resp = client.get("/api/deals/nonexistent")
    assert resp.status_code == 200
    assert "error" in resp.json()


def test_openenv_reset():
    resp = client.post("/reset", json={"task_id": "easy"})
    assert resp.status_code == 200
    data = resp.json()
    # OpenEnv wraps env state inside an "observation" object
    assert "observation" in data
    obs = data["observation"]
    assert "task_id" in obs
    assert "available_funds" in obs


def test_openenv_state():
    client.post("/reset", json={"task_id": "easy"})
    resp = client.get("/state")
    assert resp.status_code == 200

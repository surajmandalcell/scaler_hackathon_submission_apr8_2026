"""Tests for /api/admin/* CRUD, upload, and answer-key routes."""
from __future__ import annotations

from fastapi.testclient import TestClient

from fundlens.server.app import app
from fundlens.server.data_store import store

client = TestClient(app)


def _clear_store() -> None:
    resp = client.post("/api/admin/clear")
    assert resp.status_code == 200


# ── CRUD ─────────────────────────────────────────────────────────────────────


def test_create_fund_with_auto_slug():
    _clear_store()
    resp = client.post(
        "/api/admin/fund",
        json={
            "fund_name": "Manual Test Fund",
            "beginning_nav": 100.0,
            "ending_nav": 120.0,
            "reporting_date": "2024-12-31",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["fund_id"] == "manual_test_fund"
    assert "manual_test_fund" in store.funds


def test_create_deal_and_ownership():
    _clear_store()
    client.post("/api/admin/fund", json={"fund_name": "Alpha"})
    client.post(
        "/api/admin/deal",
        json={
            "property_name": "Embassy Office",
            "sector": "Office",
            "location": "Bangalore",
            "appraiser_nav": 50.0,
        },
    )
    resp = client.post(
        "/api/admin/ownership",
        json={
            "fund_id": "alpha",
            "deal_id": "embassy_office",
            "ownership_pct": 0.75,
            "entry_date": "2024-01-01",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    own = store.get_ownership("alpha", "embassy_office")
    assert own is not None
    assert abs(own.ownership_pct - 0.75) < 1e-9


def test_ownership_rejects_missing_fund():
    _clear_store()
    resp = client.post(
        "/api/admin/ownership",
        json={
            "fund_id": "ghost",
            "deal_id": "vapor",
            "ownership_pct": 1.0,
        },
    )
    assert resp.status_code == 200
    assert "error" in resp.json()


def test_create_cashflow():
    _clear_store()
    client.post("/api/admin/fund", json={"fund_name": "Alpha"})
    client.post("/api/admin/deal", json={"property_name": "Embassy"})
    resp = client.post(
        "/api/admin/cashflow",
        json={
            "fund_id": "alpha",
            "deal_id": "embassy",
            "cash_date": "2024-01-15",
            "cf_type": "contribution",
            "fund_amt": -25.0,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert any(
        c.fund_id == "alpha" and c.deal_id == "embassy" and c.fund_amt == -25.0
        for c in store.cashflows
    )


def test_cashflow_rejects_bad_cf_type():
    _clear_store()
    resp = client.post(
        "/api/admin/cashflow",
        json={
            "fund_id": "x",
            "deal_id": "y",
            "cash_date": "2024-01-01",
            "cf_type": "spaghetti",
            "fund_amt": 1.0,
        },
    )
    assert "error" in resp.json()


# ── Templates ────────────────────────────────────────────────────────────────


def test_onboarding_template_download():
    resp = client.get("/api/admin/template/onboarding")
    assert resp.status_code == 200
    assert len(resp.content) > 1000
    assert "spreadsheetml" in resp.headers.get("content-type", "")


def test_cashflow_template_download():
    resp = client.get("/api/admin/template/cashflow")
    assert resp.status_code == 200
    assert len(resp.content) > 1000


# ── Upload roundtrip ─────────────────────────────────────────────────────────


def test_onboarding_upload_roundtrip():
    """Download the template, upload it unchanged, verify bulk insertion."""
    _clear_store()

    # Download
    dl = client.get("/api/admin/template/onboarding")
    assert dl.status_code == 200

    # Upload it straight back
    up = client.post(
        "/api/admin/upload/onboarding",
        files={
            "file": (
                "onboarding.xlsx",
                dl.content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert up.status_code == 200, up.text
    body = up.json()
    # The example rows in the template should all land in the store
    assert body.get("funds_added", 0) >= 3
    assert body.get("ownerships_added", 0) >= 4
    assert len(store.funds) >= 3


def test_cashflow_upload_roundtrip():
    _clear_store()
    # Seed the referenced funds first (template references "RE Alpha Fund I" etc.)
    client.post("/api/admin/fund", json={"fund_name": "RE Alpha Fund I"})
    client.post("/api/admin/fund", json={"fund_name": "RE Beta Fund II"})

    dl = client.get("/api/admin/template/cashflow")
    up = client.post(
        "/api/admin/upload/cashflow",
        files={
            "file": (
                "cashflows.xlsx",
                dl.content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert up.status_code == 200, up.text
    body = up.json()
    assert body.get("cashflows_added", 0) >= 5


# ── Answer key ───────────────────────────────────────────────────────────────


def test_answer_key_xlsx_download():
    # Load the easy scenario so the shared store has data to export
    client.post("/api/load-scenario?task_id=easy")
    resp = client.get("/api/admin/answer-key")
    assert resp.status_code == 200
    assert len(resp.content) > 1000
    # xlsx magic bytes start with PK (it's a zip)
    assert resp.content[:2] == b"PK"


def test_answer_key_json_does_not_mutate_demo_env():
    """Calling /api/admin/answer-key/json for task X must not reset demo_env."""
    # Reset demo_env onto "hard"
    client.post("/api/session/reset", json={"task_id": "hard"})
    state_before = client.get("/api/session/state").json()
    assert state_before["task_id"] == "hard"

    # Ask for the easy answer key
    resp = client.get("/api/admin/answer-key/json?task_id=easy")
    assert resp.status_code == 200
    body = resp.json()
    assert body["task_id"] == "easy"
    assert "answers" in body
    assert len(body["answers"]) >= 1
    # One answer entry must contain a bridge + metrics block
    first_fund = next(iter(body["answers"].values()))
    assert "nav_bridge" in first_fund
    assert "metrics" in first_fund
    assert len(first_fund["nav_bridge"]) == 8

    # And demo_env must still be sitting on "hard"
    state_after = client.get("/api/session/state").json()
    assert state_after["task_id"] == "hard", "demo_env was mutated by admin answer-key!"


def test_test_run_returns_ai_and_correct():
    resp = client.post("/api/admin/test-run?task_id=easy")
    assert resp.status_code == 200
    body = resp.json()
    assert body["task_id"] == "easy"
    assert "run" in body and "correct_answers" in body
    assert body["run"]["grading"]["reward"] >= 0.9

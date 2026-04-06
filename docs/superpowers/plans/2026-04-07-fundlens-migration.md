# FundLens Migration & React Frontend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace FridgeEnv with FundLens as the primary hackathon submission — restructure into monorepo, build React frontend, add code quality tooling.

**Architecture:** Monorepo with `packages/backend` (Python/FastAPI/OpenEnv) and `packages/frontend` (React/Vite). Backend serves the OpenEnv MCP environment + REST API endpoints for the frontend. Frontend is a single-page React app with 5 pages. Docker multi-stage build combines both.

**Tech Stack:** Python 3.11, FastAPI, openenv-core, FastMCP, Pydantic v2 | React 18, Vite 6, Vitest | Docker multi-stage

---

## File Map

### Files to Create
- `packages/backend/pyproject.toml` — package config + ruff + mypy
- `packages/backend/fundlens/__init__.py` — package marker
- `packages/backend/fundlens/models.py` — Pydantic models (copy from fundlens/)
- `packages/backend/fundlens/client.py` — MCP client (copy from fundlens/)
- `packages/backend/fundlens/server/__init__.py` — package marker
- `packages/backend/fundlens/server/app.py` — FastAPI app (rewritten, no Gradio)
- `packages/backend/fundlens/server/environment.py` — MCP tools (copy from fundlens/)
- `packages/backend/fundlens/server/calculations.py` — XIRR + NAV bridge (copy)
- `packages/backend/fundlens/server/grader.py` — scoring (copy)
- `packages/backend/fundlens/server/seed_data.py` — 3 scenarios (copy)
- `packages/backend/fundlens/server/data_store.py` — data store (copy)
- `packages/backend/tests/__init__.py`
- `packages/backend/tests/test_calculations.py` — copy + expand
- `packages/backend/tests/test_grader.py` — copy + expand
- `packages/backend/tests/test_environment.py` — copy + expand
- `packages/backend/tests/test_api.py` — new: REST API endpoint tests
- `packages/backend/tests/test_seed_data.py` — new: seed data integrity
- `packages/backend/tests/test_data_store.py` — new: data store operations
- `packages/frontend/src/index.css` — finance design system
- `packages/frontend/src/App.jsx` — router with 5 pages
- `packages/frontend/src/components/Dashboard.jsx`
- `packages/frontend/src/components/NAVBridge.jsx`
- `packages/frontend/src/components/FundExplorer.jsx`
- `packages/frontend/src/components/AgentRunner.jsx`
- `packages/frontend/src/components/DocsPage.jsx`
- `packages/frontend/src/components/ScoreCard.jsx`
- `packages/frontend/src/App.test.jsx`
- `packages/frontend/src/components/Dashboard.test.jsx`
- `packages/frontend/src/components/NAVBridge.test.jsx`
- `packages/frontend/src/components/ScoreCard.test.jsx`

### Files to Modify
- `package.json` — update scripts for FundLens
- `packages/frontend/package.json` — rename to @fundlens/frontend
- `packages/frontend/index.html` — update title + fonts
- `packages/frontend/vite.config.js` — update proxy routes
- `packages/frontend/src/main.jsx` — keep as-is (mounts App)
- `inference.py` — replace with FundLens version
- `openenv.yaml` — replace with FundLens manifest
- `Dockerfile` — rewrite for multi-stage FundLens build
- `README.md` — replace with FundLens docs
- `.env.example` — update for FundLens env vars
- `.gitignore` — add Python patterns

### Files to Delete
- `packages/backend/env/` — entire FridgeEnv environment
- `packages/backend/agents/` — FridgeEnv agents
- `packages/backend/app.py` — FridgeEnv FastAPI server
- `packages/backend/pyproject.toml` (old, if exists)
- `packages/frontend/src/components/FridgeView.jsx` + test
- `packages/frontend/src/components/MealTimeline.jsx` + test
- `packages/frontend/src/components/MealPlanner.jsx` + test
- `packages/frontend/src/components/CustomInventory.jsx` + test
- `packages/frontend/src/components/ScoreCard.jsx` + test (old FridgeEnv version)
- `packages/frontend/src/components/DocsPage.jsx` + test (old FridgeEnv version)
- `packages/frontend/src/App.jsx` + test (old FridgeEnv version)
- `packages/frontend/src/index.css` (old design system)
- `EXPLANATION.md` (old FridgeEnv version)
- `fundlens/` — entire nested directory (source moved to packages/backend)

---

## Task 1: Clean Out FridgeEnv Files

**Files:**
- Delete: `packages/backend/env/`, `packages/backend/agents/`, `packages/backend/app.py`
- Delete: `packages/frontend/src/components/FridgeView.jsx`, `MealTimeline.jsx`, `MealPlanner.jsx`, `CustomInventory.jsx`, `ScoreCard.jsx`, `DocsPage.jsx` + all `.test.jsx` files
- Delete: `packages/frontend/src/App.jsx`, `packages/frontend/src/App.test.jsx`
- Delete: `packages/frontend/src/index.css`

- [ ] **Step 1: Delete FridgeEnv backend files**

```bash
rm -rf packages/backend/env packages/backend/agents packages/backend/app.py
rm -rf packages/backend/tests packages/backend/__pycache__
rm -f packages/backend/inference.py 2>/dev/null
```

- [ ] **Step 2: Delete FridgeEnv frontend files**

```bash
rm -f packages/frontend/src/components/FridgeView.jsx
rm -f packages/frontend/src/components/FridgeView.test.jsx
rm -f packages/frontend/src/components/MealTimeline.jsx
rm -f packages/frontend/src/components/MealTimeline.test.jsx
rm -f packages/frontend/src/components/MealPlanner.jsx
rm -f packages/frontend/src/components/MealPlanner.test.jsx
rm -f packages/frontend/src/components/CustomInventory.jsx
rm -f packages/frontend/src/components/CustomInventory.test.jsx
rm -f packages/frontend/src/components/ScoreCard.jsx
rm -f packages/frontend/src/components/ScoreCard.test.jsx
rm -f packages/frontend/src/components/DocsPage.jsx
rm -f packages/frontend/src/components/DocsPage.test.jsx
rm -f packages/frontend/src/App.jsx
rm -f packages/frontend/src/App.test.jsx
rm -f packages/frontend/src/index.css
```

- [ ] **Step 3: Delete old root-level FridgeEnv files**

```bash
rm -f EXPLANATION.md
```

- [ ] **Step 4: Commit cleanup**

```bash
git add -A
git commit -m "chore: remove FridgeEnv files to prepare for FundLens migration"
```

---

## Task 2: Move FundLens Backend Into Monorepo

**Files:**
- Create: `packages/backend/pyproject.toml`
- Create: `packages/backend/fundlens/` (entire package tree)
- Create: `packages/backend/agents/` (multi-agent system)
- Create: `packages/backend/tests/` (existing tests)

- [ ] **Step 1: Create backend package directory structure**

```bash
mkdir -p packages/backend/fundlens/server
mkdir -p packages/backend/agents
mkdir -p packages/backend/tests
```

- [ ] **Step 2: Copy FundLens Python package**

```bash
cp fundlens/fundlens/__init__.py packages/backend/fundlens/
cp fundlens/fundlens/models.py packages/backend/fundlens/
cp fundlens/fundlens/client.py packages/backend/fundlens/
cp fundlens/fundlens/server/__init__.py packages/backend/fundlens/server/
cp fundlens/fundlens/server/environment.py packages/backend/fundlens/server/
cp fundlens/fundlens/server/calculations.py packages/backend/fundlens/server/
cp fundlens/fundlens/server/grader.py packages/backend/fundlens/server/
cp fundlens/fundlens/server/seed_data.py packages/backend/fundlens/server/
cp fundlens/fundlens/server/data_store.py packages/backend/fundlens/server/
```

- [ ] **Step 3: Copy agents directory**

```bash
cp fundlens/agents/*.py packages/backend/agents/
```

- [ ] **Step 4: Copy existing tests**

```bash
cp fundlens/tests/__init__.py packages/backend/tests/
cp fundlens/tests/test_calculations.py packages/backend/tests/
cp fundlens/tests/test_grader.py packages/backend/tests/
cp fundlens/tests/test_environment.py packages/backend/tests/
```

- [ ] **Step 5: Create pyproject.toml with ruff + mypy config**

Write `packages/backend/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "fundlens"
version = "0.1.0"
description = "PE Fund NAV Bridge & Reporting OpenEnv Environment"
requires-python = ">=3.10"
dependencies = [
    "openenv-core>=0.2.3",
    "fastmcp>=3.1.1",
    "pydantic>=2.0",
    "fastapi",
    "uvicorn",
    "openai",
    "httpx",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["fundlens*"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 6: Install backend dependencies**

```bash
cd packages/backend && pip install -e ".[dev]"
```

- [ ] **Step 7: Verify existing tests pass**

```bash
cd packages/backend && python -m pytest tests/ -v
```

Expected: all existing tests pass (test_calculations, test_grader, test_environment).

- [ ] **Step 8: Commit backend migration**

```bash
git add packages/backend/
git commit -m "feat: migrate FundLens backend into packages/backend monorepo structure"
```

---

## Task 3: Rewrite Backend app.py (No Gradio, Add REST API)

**Files:**
- Create: `packages/backend/fundlens/server/app.py` (rewrite)

- [ ] **Step 1: Write the new app.py with REST API endpoints**

Write `packages/backend/fundlens/server/app.py`:

```python
"""FastAPI application -- OpenEnv API + REST endpoints for React frontend."""
from __future__ import annotations
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from openenv.core.env_server import create_app, CallToolAction
from fundlens.models import FundLensObservation
from fundlens.server.environment import FundLensEnvironment
from fundlens.server.data_store import DataStore
from fundlens.server.calculations import compute_nav_bridge, compute_metrics
from fundlens.server.seed_data import load_easy_task, load_medium_task, load_hard_task
import os

# OpenEnv HTTP API (reset / step / state endpoints)
app = create_app(
    env=FundLensEnvironment,
    action_cls=CallToolAction,
    observation_cls=FundLensObservation,
    env_name="fundlens",
)

# Shared data store for REST API queries
_api_store = DataStore()

_LOADERS = {
    "easy": load_easy_task,
    "medium": load_medium_task,
    "hard": load_hard_task,
}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/load-scenario")
async def load_scenario(task_id: str = "easy") -> dict:
    """Load seed data for a difficulty level into the shared API store."""
    loader = _LOADERS.get(task_id, load_easy_task)
    loader(_api_store)
    fund_ids = list(_api_store.funds.keys())
    return {
        "task_id": task_id,
        "funds_loaded": fund_ids,
        "fund_count": len(fund_ids),
    }


@app.get("/api/portfolio")
async def get_portfolio() -> dict:
    """Portfolio summary -- fund-level NAV, MOIC, IRR."""
    result = {}
    for fid, fund in _api_store.funds.items():
        metrics = compute_metrics(fid, _api_store)
        result[fid] = {
            "fund_name": fund.fund_name,
            "beginning_nav": round(fund.beginning_nav, 4),
            "ending_nav": round(fund.ending_nav, 4),
            "reporting_date": fund.reporting_date,
            **{k: round(v, 4) for k, v in metrics.items()},
        }
    return result


@app.get("/api/bridge/{fund_id}")
async def get_bridge(fund_id: str) -> dict:
    """8-line NAV bridge for a fund."""
    bridge = compute_nav_bridge(fund_id, _api_store)
    if not bridge:
        return {"error": f"Fund '{fund_id}' not found"}
    return {k: round(v, 4) for k, v in bridge.items()}


@app.get("/api/deals/{fund_id}")
async def get_deals(fund_id: str) -> dict:
    """Deals + ownership for a fund."""
    if fund_id not in _api_store.funds:
        return {"error": f"Fund '{fund_id}' not found"}
    deals = []
    for deal in _api_store.get_deals_for_fund(fund_id):
        own = _api_store.get_ownership(fund_id, deal.deal_id)
        cfs = _api_store.get_cashflows(fund_id=fund_id, deal_id=deal.deal_id)
        invested = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
        received = sum(c.fund_amt for c in cfs if c.cf_type in ("disposition", "income"))
        deals.append({
            "deal_id": deal.deal_id,
            "property_name": deal.property_name,
            "sector": deal.sector,
            "location": deal.location,
            "ownership_pct": own.ownership_pct if own else 1.0,
            "appraiser_nav": round(deal.appraiser_nav, 4),
            "invested": round(invested, 4),
            "received": round(received, 4),
        })
    return {"fund_id": fund_id, "deals": deals}


@app.get("/api/cashflows/{fund_id}")
async def get_cashflows(fund_id: str, deal_id: Optional[str] = None) -> dict:
    """Cashflow summary for a fund or specific deal."""
    cfs = _api_store.get_cashflows(fund_id=fund_id, deal_id=deal_id)
    total_contribution = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
    total_disposition = sum(c.fund_amt for c in cfs if c.cf_type == "disposition")
    total_income = sum(c.fund_amt for c in cfs if c.cf_type == "income")
    records = sorted(
        [{"date": c.cash_date, "deal_id": c.deal_id, "type": c.cf_type,
          "amount": round(c.fund_amt, 4)} for c in cfs],
        key=lambda r: r["date"],
    )
    return {
        "fund_id": fund_id,
        "total_contribution": round(total_contribution, 4),
        "total_disposition": round(total_disposition, 4),
        "total_income": round(total_income, 4),
        "records": records,
    }


@app.get("/api/sectors")
async def get_sectors() -> dict:
    """Sector breakdown across all funds."""
    sector_data = {}
    for fid in _api_store.funds:
        for deal in _api_store.get_deals_for_fund(fid):
            sec = deal.sector
            if sec not in sector_data:
                sector_data[sec] = {"total_invested": 0.0, "total_received": 0.0, "deal_count": 0}
            cfs = _api_store.get_cashflows(fund_id=fid, deal_id=deal.deal_id)
            sector_data[sec]["total_invested"] += sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
            sector_data[sec]["total_received"] += sum(c.fund_amt for c in cfs if c.cf_type in ("disposition", "income"))
            sector_data[sec]["deal_count"] += 1
    for v in sector_data.values():
        v["total_invested"] = round(v["total_invested"], 4)
        v["total_received"] = round(v["total_received"], 4)
    return sector_data


# Serve React frontend (must be LAST -- catches all unmatched routes)
_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "frontend", "dist")
if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = os.path.join(_DIST, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_DIST, "index.html"))
```

- [ ] **Step 2: Verify server starts**

```bash
cd packages/backend && python -m uvicorn fundlens.server.app:app --host 0.0.0.0 --port 7860 &
sleep 2
curl http://localhost:7860/health
kill %1
```

Expected: `{"status":"ok"}`

- [ ] **Step 3: Commit**

```bash
git add packages/backend/fundlens/server/app.py
git commit -m "feat: rewrite app.py with REST API endpoints, remove Gradio"
```

---

## Task 4: Write REST API Tests

**Files:**
- Create: `packages/backend/tests/test_api.py`
- Create: `packages/backend/tests/test_seed_data.py`
- Create: `packages/backend/tests/test_data_store.py`

- [ ] **Step 1: Write test_api.py**

```python
"""Tests for REST API endpoints."""
import pytest
from fastapi.testclient import TestClient
from fundlens.server.app import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


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
    assert "task_id" in data
    assert "available_funds" in data


def test_openenv_state():
    client.post("/reset", json={"task_id": "easy"})
    resp = client.get("/state")
    assert resp.status_code == 200
```

- [ ] **Step 2: Write test_seed_data.py**

```python
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
```

- [ ] **Step 3: Write test_data_store.py**

```python
"""Tests for DataStore operations."""
import pytest
from fundlens.server.data_store import DataStore
from fundlens.models import Fund, Deal, Ownership, Cashflow


def test_add_and_get_fund():
    s = DataStore()
    s.add_fund(Fund(fund_id="f1", fund_name="Test", reporting_date="2024-12-31",
                    beginning_nav=10.0, ending_nav=15.0))
    assert "f1" in s.funds
    assert s.funds["f1"].fund_name == "Test"


def test_add_and_get_deal():
    s = DataStore()
    s.add_deal(Deal(deal_id="d1", property_name="Prop", sector="Office", location="NYC"))
    assert "d1" in s.deals


def test_add_ownership():
    s = DataStore()
    s.add_fund(Fund(fund_id="f1", fund_name="T", reporting_date="2024-12-31",
                    beginning_nav=10.0, ending_nav=15.0))
    s.add_deal(Deal(deal_id="d1", property_name="P", sector="Office", location="NYC"))
    s.add_ownership(Ownership(deal_id="d1", fund_id="f1", ownership_pct=0.65, entry_date="2022-01-01"))
    own = s.get_ownership("f1", "d1")
    assert own is not None
    assert own.ownership_pct == 0.65


def test_get_cashflows_by_fund():
    s = DataStore()
    s.add_cashflow(Cashflow(cashflow_id="c1", deal_id="d1", fund_id="f1",
                            cash_date="2024-01-01", cf_type="contribution", fund_amt=-5.0))
    s.add_cashflow(Cashflow(cashflow_id="c2", deal_id="d1", fund_id="f2",
                            cash_date="2024-01-01", cf_type="contribution", fund_amt=-3.0))
    cfs = s.get_cashflows(fund_id="f1")
    assert len(cfs) == 1
    assert cfs[0].fund_amt == -5.0


def test_get_cashflows_by_deal():
    s = DataStore()
    s.add_cashflow(Cashflow(cashflow_id="c1", deal_id="d1", fund_id="f1",
                            cash_date="2024-01-01", cf_type="contribution", fund_amt=-5.0))
    s.add_cashflow(Cashflow(cashflow_id="c2", deal_id="d2", fund_id="f1",
                            cash_date="2024-01-01", cf_type="contribution", fund_amt=-3.0))
    cfs = s.get_cashflows(fund_id="f1", deal_id="d1")
    assert len(cfs) == 1


def test_get_deals_for_fund():
    s = DataStore()
    s.add_fund(Fund(fund_id="f1", fund_name="T", reporting_date="2024-12-31",
                    beginning_nav=10.0, ending_nav=15.0))
    s.add_deal(Deal(deal_id="d1", property_name="P1", sector="Office", location="NYC"))
    s.add_deal(Deal(deal_id="d2", property_name="P2", sector="Residential", location="LA"))
    s.add_ownership(Ownership(deal_id="d1", fund_id="f1", ownership_pct=1.0, entry_date="2022-01-01"))
    s.add_ownership(Ownership(deal_id="d2", fund_id="f1", ownership_pct=0.5, entry_date="2022-01-01"))
    deals = s.get_deals_for_fund("f1")
    assert len(deals) == 2


def test_clear_resets_all():
    s = DataStore()
    s.add_fund(Fund(fund_id="f1", fund_name="T", reporting_date="2024-12-31",
                    beginning_nav=10.0, ending_nav=15.0))
    s.clear()
    assert len(s.funds) == 0
```

- [ ] **Step 4: Run all tests**

```bash
cd packages/backend && python -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add packages/backend/tests/
git commit -m "test: add API, seed data, and data store tests"
```

---

## Task 5: Update Root Files (inference.py, openenv.yaml, .env, .gitignore)

**Files:**
- Modify: `inference.py`, `openenv.yaml`, `.env.example`, `.gitignore`

- [ ] **Step 1: Replace inference.py with FundLens version**

```bash
cp fundlens/inference.py ./inference.py
```

Update the import to work from root (the import paths should work since packages/backend is installed editable).

- [ ] **Step 2: Replace openenv.yaml**

Write `openenv.yaml`:

```yaml
name: fundlens
version: 0.2.0
description: >
  RE Fund NAV Bridge & Performance Environment.
  AI agents compute NAV bridges and performance metrics
  for real estate private equity funds.
tasks:
  - id: easy
    description: "RE Alpha Fund I — 3 properties, 100% owned, NAV bridge only"
    difficulty: easy
    graded_items: 8
  - id: medium
    description: "RE Beta Fund II — 5 properties, NAV bridge + MOIC"
    difficulty: medium
    graded_items: 9
  - id: hard
    description: "Cross-fund portfolio — 3 funds, co-investment, NAV bridge + MOIC + IRR"
    difficulty: hard
    graded_items: 10
action_space: MCP tool calls (CallToolAction)
observation_space: Tool responses as JSON (FundLensObservation)
reward_range: [0.0, 1.0]
entry_point: fundlens.server.app:app
```

- [ ] **Step 3: Update .env.example**

```
# LLM API (OpenAI-compatible endpoint)
API_BASE_URL=https://router.huggingface.co/v1
OPENAI_API_KEY=sk-your-key-here
MODEL_NAME=nvidia/Llama-3.1-Nemotron-70B-Instruct-HF

# FundLens server
ENV_SERVER_URL=http://localhost:7860

# Hugging Face
HF_TOKEN=hf_your-token-here
```

- [ ] **Step 4: Update .gitignore to include Python patterns**

Append these lines to `.gitignore`:

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
*.egg
dist/
build/
.eggs/
*.db
.mypy_cache/
.ruff_cache/
.pytest_cache/

# Environment
.env
.venv/
venv/

# IDE
.vscode/
.idea/

# OS
.DS_Store

# Node
node_modules/
packages/frontend/dist/
```

- [ ] **Step 5: Remove .env from git tracking (critical security fix)**

```bash
git rm --cached .env 2>/dev/null || true
```

- [ ] **Step 6: Commit**

```bash
git add inference.py openenv.yaml .env.example .gitignore
git commit -m "feat: replace root files with FundLens versions, fix credential exposure"
```

---

## Task 6: Update Root package.json

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Rewrite package.json for FundLens**

```json
{
  "name": "fundlens",
  "version": "1.0.0",
  "private": true,
  "workspaces": [
    "packages/*"
  ],
  "scripts": {
    "install:backend": "cd packages/backend && pip install -e '.[dev]'",
    "install:all": "npm install && npm run install:backend",

    "test": "npm run test:backend",
    "test:backend": "cd packages/backend && python -m pytest tests/ -v",
    "test:frontend": "npm test -w packages/frontend",
    "test:all": "npm run test:backend && npm run test:frontend",

    "lint": "cd packages/backend && ruff check .",
    "lint:fix": "cd packages/backend && ruff check --fix . && ruff format .",
    "typecheck": "cd packages/backend && mypy fundlens/",

    "dev": "cd packages/backend && uvicorn fundlens.server.app:app --host 0.0.0.0 --port 7860 --reload",
    "dev:frontend": "npm run dev -w packages/frontend",

    "build": "npm run build -w packages/frontend",
    "docker:build": "docker build -t fundlens .",
    "docker:run": "docker run --rm -p 27860:7860 fundlens",

    "inference": "cd packages/backend && python ../../inference.py",

    "preflight": "npm run lint && npm run typecheck && npm run test:all && npm run build"
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add package.json
git commit -m "chore: update root package.json for FundLens monorepo"
```

---

## Task 7: Build React Frontend -- Design System + Shell

**Files:**
- Modify: `packages/frontend/index.html`, `packages/frontend/package.json`, `packages/frontend/vite.config.js`
- Create: `packages/frontend/src/index.css`, `packages/frontend/src/App.jsx`, `packages/frontend/src/main.jsx`

- [ ] **Step 1: Update packages/frontend/package.json**

```json
{
  "name": "@fundlens/frontend",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.9.1",
    "@testing-library/react": "^16.3.2",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "jsdom": "^29.0.1",
    "vite": "^6.0.0",
    "vitest": "^3.0.0"
  }
}
```

- [ ] **Step 2: Update index.html**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>FundLens — PE Fund Reporting Environment</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 3: Update vite.config.js**

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/reset": "http://localhost:7860",
      "/step": "http://localhost:7860",
      "/state": "http://localhost:7860",
      "/health": "http://localhost:7860",
      "/api": "http://localhost:7860",
      "/metadata": "http://localhost:7860",
      "/schema": "http://localhost:7860",
    },
  },
  build: {
    outDir: "dist",
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test-setup.js",
  },
});
```

- [ ] **Step 4: Write the finance design system (index.css)**

Write `packages/frontend/src/index.css` — full CSS with the deep blue/emerald finance palette, DM Serif Display headings, Plus Jakarta Sans body, JetBrains Mono for data. Include:
- CSS custom properties for all colors, fonts, radii
- Base reset + body styles
- Scrollbar + selection styles
- Enter/reveal animations
- Table styles with alternating row opacity
- Card styles with left-border accent bars
- Positive (emerald) and negative (red) value highlight classes

- [ ] **Step 5: Write App.jsx with page routing**

Write `packages/frontend/src/App.jsx` — single-page app with tab navigation between Dashboard, NAV Bridge, Explorer, Agent Runner, and Docs pages. State: `page`, `taskId`, `scenario` (loaded data), `loading`.

- [ ] **Step 6: Verify frontend dev server starts**

```bash
cd packages/frontend && npm run dev &
sleep 3
curl http://localhost:5173
kill %1
```

- [ ] **Step 7: Commit**

```bash
git add packages/frontend/
git commit -m "feat: frontend shell with finance design system and page routing"
```

---

## Task 8: Build Frontend Components -- Dashboard + ScoreCard

**Files:**
- Create: `packages/frontend/src/components/Dashboard.jsx`
- Create: `packages/frontend/src/components/ScoreCard.jsx`

- [ ] **Step 1: Write Dashboard.jsx**

Dashboard component that:
- Shows difficulty toggle (Easy/Medium/Hard)
- "Load Scenario" button that POSTs to `/api/load-scenario?task_id=X`
- After loading, shows fund cards with: name, NAV movement (beginning -> ending $M), MOIC badge, IRR badge
- Mode indicator showing what gets graded at current difficulty
- Conditional display: MOIC only shown for medium+, IRR only for hard
- Uses the finance design system CSS classes

- [ ] **Step 2: Write ScoreCard.jsx**

ScoreCard component that:
- Displays overall reward (0.0-1.0) prominently
- Shows bridge_score and metrics_score breakdowns
- Per-item results if available (green check / red X per bridge line item)
- Accepts `result` prop with grading data

- [ ] **Step 3: Write Dashboard.test.jsx**

```jsx
import { render, screen } from "@testing-library/react";
import Dashboard from "./Dashboard";

test("renders difficulty buttons", () => {
  render(<Dashboard onLoadScenario={() => {}} />);
  expect(screen.getByText("Easy")).toBeInTheDocument();
  expect(screen.getByText("Medium")).toBeInTheDocument();
  expect(screen.getByText("Hard")).toBeInTheDocument();
});

test("renders load button", () => {
  render(<Dashboard onLoadScenario={() => {}} />);
  expect(screen.getByText("Load Scenario")).toBeInTheDocument();
});

test("shows fund cards when data provided", () => {
  const portfolio = {
    alpha: { fund_name: "RE Alpha Fund I", beginning_nav: 100, ending_nav: 120, moic: 1.5, irr: 0.12 }
  };
  render(<Dashboard portfolio={portfolio} taskId="easy" onLoadScenario={() => {}} />);
  expect(screen.getByText("RE Alpha Fund I")).toBeInTheDocument();
});
```

- [ ] **Step 4: Write ScoreCard.test.jsx**

```jsx
import { render, screen } from "@testing-library/react";
import ScoreCard from "./ScoreCard";

test("renders reward score", () => {
  render(<ScoreCard result={{ reward: 0.875, bridge_score: 7, metrics_score: 1 }} />);
  expect(screen.getByText(/0.875/)).toBeInTheDocument();
});

test("renders nothing when no result", () => {
  const { container } = render(<ScoreCard result={null} />);
  expect(container.firstChild).toBeNull();
});
```

- [ ] **Step 5: Run frontend tests**

```bash
cd packages/frontend && npx vitest run
```

- [ ] **Step 6: Commit**

```bash
git add packages/frontend/src/components/Dashboard.jsx packages/frontend/src/components/ScoreCard.jsx
git add packages/frontend/src/components/Dashboard.test.jsx packages/frontend/src/components/ScoreCard.test.jsx
git commit -m "feat: Dashboard and ScoreCard components"
```

---

## Task 9: Build Frontend Components -- NAVBridge + FundExplorer

**Files:**
- Create: `packages/frontend/src/components/NAVBridge.jsx`
- Create: `packages/frontend/src/components/FundExplorer.jsx`

- [ ] **Step 1: Write NAVBridge.jsx**

NAVBridge component that:
- Takes fund selector (dropdown of fund_ids from loaded scenario)
- Fetches bridge data from `GET /api/bridge/{fund_id}`
- Displays 8-row table: Step | Amount ($M) | What this means
- Each row has: label (e.g. "(+) Capital Called"), formatted dollar amount, plain-English explanation
- Rows color-coded: additions get emerald left border, subtractions get red, totals get blue
- "cashflow_adjusted_nav" and "ending_nav" rows are bold subtotals

Bridge item labels and explanations map:
```
beginning_nav         -> "Opening Value"         -> "Where the fund started this period"
contribution          -> "(+) Capital Called"     -> "New capital deployed into properties"
disposition           -> "(-) Sales Proceeds"     -> "Cash received from property sales"
income                -> "(+) Income Received"    -> "Rental and operating income collected"
cashflow_adjusted_nav -> "= Cash-Adjusted Value"  -> "NAV after all cash movements"
income_reversal       -> "(-) Income Reversal"    -> "Income added back (already in valuation)"
write_up_down         -> "(+/-) Value Change"     -> "Net change in property valuations (the plug)"
ending_nav            -> "= Closing Value"        -> "Fund value at end of period"
```

- [ ] **Step 2: Write FundExplorer.jsx**

FundExplorer component that:
- Fund selector dropdown
- Fetches deals from `GET /api/deals/{fund_id}` and cashflows from `GET /api/cashflows/{fund_id}`
- Deals table: Property | Sector | Location | Ownership | Capital In | Cash Out
- Cashflow summary: total contribution, disposition, income displayed as metric cards
- Sector breakdown from `GET /api/sectors` shown as small cards

- [ ] **Step 3: Write NAVBridge.test.jsx**

```jsx
import { render, screen } from "@testing-library/react";
import NAVBridge from "./NAVBridge";

test("renders bridge table when data provided", () => {
  const bridge = {
    beginning_nav: 100, contribution: 20, disposition: 5, income: 3,
    cashflow_adjusted_nav: 118, income_reversal: -3, write_up_down: 5, ending_nav: 120,
  };
  render(<NAVBridge bridge={bridge} />);
  expect(screen.getByText("Opening Value")).toBeInTheDocument();
  expect(screen.getByText("= Closing Value")).toBeInTheDocument();
});

test("renders empty state when no bridge", () => {
  render(<NAVBridge bridge={null} />);
  expect(screen.getByText(/select a fund/i)).toBeInTheDocument();
});
```

- [ ] **Step 4: Run tests**

```bash
cd packages/frontend && npx vitest run
```

- [ ] **Step 5: Commit**

```bash
git add packages/frontend/src/components/NAVBridge.jsx packages/frontend/src/components/FundExplorer.jsx
git add packages/frontend/src/components/NAVBridge.test.jsx
git commit -m "feat: NAVBridge and FundExplorer components"
```

---

## Task 10: Build Frontend Components -- AgentRunner + DocsPage

**Files:**
- Create: `packages/frontend/src/components/AgentRunner.jsx`
- Create: `packages/frontend/src/components/DocsPage.jsx`

- [ ] **Step 1: Write AgentRunner.jsx**

AgentRunner component that:
- "Run Agent" button that:
  1. POSTs `/reset` with current task_id -> gets observation
  2. Iteratively POSTs `/step` with CallToolAction payloads
  3. Shows each step in a scrollable log (tool_name, arguments summary, result snippet)
  4. Stops when `is_done` is true or max steps reached
- Displays final ScoreCard with grading result
- Simple agent strategy: calls get_nav_bridge, then submit_report with the result (like a pass-through baseline)

- [ ] **Step 2: Write DocsPage.jsx**

DocsPage component with:
- API Endpoints table (GET/POST, path, description)
- Data Models section (Fund, Deal, Ownership, Cashflow fields)
- Grading Tolerances table: Amounts +-$0.5M, MOIC +-0.02x, IRR +-1%
- NAV Bridge formula walkthrough (the 8 lines explained)
- Difficulty levels: what gets graded at each level

- [ ] **Step 3: Commit**

```bash
git add packages/frontend/src/components/AgentRunner.jsx packages/frontend/src/components/DocsPage.jsx
git commit -m "feat: AgentRunner and DocsPage components"
```

---

## Task 11: Write Dockerfile (Multi-Stage)

**Files:**
- Modify: `Dockerfile`

- [ ] **Step 1: Write multi-stage Dockerfile**

```dockerfile
# Stage 1: Build React frontend
FROM node:20-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
COPY packages/frontend/package.json packages/frontend/
RUN npm ci --workspace=packages/frontend
COPY packages/frontend/ packages/frontend/
RUN npm run build -w packages/frontend

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY packages/backend/pyproject.toml packages/backend/
RUN pip install --no-cache-dir -e packages/backend/ 2>/dev/null || true
COPY packages/backend/ packages/backend/
RUN pip install --no-cache-dir -e packages/backend/

# Copy built frontend
COPY --from=frontend /app/packages/frontend/dist packages/frontend/dist

# Copy root files
COPY inference.py openenv.yaml ./

EXPOSE 7860

CMD ["uvicorn", "fundlens.server.app:app", "--host", "0.0.0.0", "--port", "7860"]
```

- [ ] **Step 2: Update .dockerignore**

```
.git
.env
node_modules
__pycache__
*.pyc
.mypy_cache
.ruff_cache
.pytest_cache
fundlens/
*.xlsx
*.db
```

- [ ] **Step 3: Test Docker build**

```bash
docker build -t fundlens .
```

- [ ] **Step 4: Test Docker run**

```bash
docker run --rm -p 27860:7860 fundlens &
sleep 3
curl http://localhost:27860/health
curl -X POST http://localhost:27860/reset -H "Content-Type: application/json" -d '{"task_id":"easy"}'
docker stop $(docker ps -q --filter ancestor=fundlens)
```

Expected: health returns `{"status":"ok"}`, reset returns observation JSON.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "feat: multi-stage Dockerfile for FundLens (Node build + Python runtime)"
```

---

## Task 12: Write README.md + EXPLANATION.md

**Files:**
- Modify: `README.md`
- Create: `EXPLANATION.md`

- [ ] **Step 1: Write README.md**

Cover: problem motivation (PE fund NAV bridge reconciliation), environment description, 3 difficulty levels table, NAV bridge formula, action/observation spaces, MCP tools list (15 tools), grading tolerances, baseline scores, setup instructions (local + Docker), project structure, tech stack.

- [ ] **Step 2: Write EXPLANATION.md**

Plain-English explanation of: what an OpenEnv environment is, what FundLens does, how NAV bridges work, what the 3 difficulty levels test, how scoring works, what judges evaluate.

- [ ] **Step 3: Commit**

```bash
git add README.md EXPLANATION.md
git commit -m "docs: comprehensive README and EXPLANATION for FundLens submission"
```

---

## Task 13: Delete fundlens/ Source Directory

After migration is verified, remove the source directory.

- [ ] **Step 1: Verify all tests pass from monorepo**

```bash
npm run test:all
npm run build
```

- [ ] **Step 2: Delete source directory**

```bash
rm -rf fundlens/
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove fundlens source directory after migration to packages/"
```

---

## Task 14: Final Preflight + Verification

- [ ] **Step 1: Run full preflight**

```bash
npm run preflight
```

Expected: lint passes, typecheck passes, all backend tests pass, all frontend tests pass, build succeeds.

- [ ] **Step 2: Docker end-to-end**

```bash
docker build -t fundlens . && docker run --rm -p 27860:7860 fundlens &
sleep 5
curl http://localhost:27860/health
curl -X POST http://localhost:27860/api/load-scenario?task_id=easy
curl http://localhost:27860/api/portfolio
curl http://localhost:27860/api/bridge/alpha
docker stop $(docker ps -q --filter ancestor=fundlens)
```

- [ ] **Step 3: Visit React UI in browser**

Open http://localhost:27860, verify:
- Dashboard loads, difficulty toggle works
- Load Scenario loads fund data
- NAV Bridge page shows 8-line table
- Explorer shows deals and cashflows
- Docs page renders fully

- [ ] **Step 4: Run inference.py**

```bash
npm run inference
```

Expected: completes 3 tasks with scores in [0.0, 1.0], no errors.

- [ ] **Step 5: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: final verification fixes"
```

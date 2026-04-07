"""FastAPI application -- OpenEnv API + REST endpoints for React frontend."""
from __future__ import annotations

import os
from typing import Any

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openenv.core.env_server import CallToolAction, create_app

from fundlens.models import FundLensObservation
from fundlens.server.calculations import compute_metrics, compute_nav_bridge
from fundlens.server.data_store import store
from fundlens.server.environment import FundLensEnvironment
from fundlens.server.runtime import demo_env, unwrap_tool_result
from fundlens.server.seed_data import load_easy_task, load_hard_task, load_medium_task

# OpenEnv HTTP API (reset / step / state endpoints)
app = create_app(
    env=FundLensEnvironment,
    action_cls=CallToolAction,
    observation_cls=FundLensObservation,
    env_name="fundlens",
)

# Mount additional routers (session playground, admin CRUD / uploads)
from fundlens.admin.routes import router as admin_router  # noqa: E402
from fundlens.server.session_routes import router as session_router  # noqa: E402

app.include_router(session_router)
app.include_router(admin_router)

_LOADERS = {
    "easy": load_easy_task,
    "medium": load_medium_task,
    "hard": load_hard_task,
}


@app.get("/health")
async def health() -> dict:
    """Health check for container orchestration / HuggingFace Space."""
    return {"status": "ok"}


@app.post("/api/load-scenario")
async def load_scenario(task_id: str = "easy") -> dict:
    """Load seed data for a difficulty level into the shared store.

    Also resets the long-lived `demo_env` so the Playground and
    `/api/run-agent` observe the same scenario the Analyst view is looking at.
    """
    loader = _LOADERS.get(task_id, load_easy_task)
    loader(store)
    # Sync the playground env's task_id + correct answers without re-loading
    # the store (which `loader` already did against the shared instance).
    demo_env.reset(task_id=task_id)
    fund_ids = list(store.funds.keys())
    return {
        "task_id": task_id,
        "funds_loaded": fund_ids,
        "fund_count": len(fund_ids),
    }


@app.get("/api/portfolio")
async def get_portfolio() -> dict:
    """Portfolio summary -- fund-level NAV, MOIC, IRR."""
    result = {}
    for fid, fund in store.funds.items():
        metrics = compute_metrics(fid, store)
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
    bridge = compute_nav_bridge(fund_id, store)
    if not bridge:
        return {"error": f"Fund '{fund_id}' not found"}
    return {k: round(v, 4) for k, v in bridge.items()}


@app.get("/api/deals/{fund_id}")
async def get_deals(fund_id: str) -> dict:
    """Deals + ownership for a fund."""
    if fund_id not in store.funds:
        return {"error": f"Fund '{fund_id}' not found"}
    deals = []
    for deal in store.get_deals_for_fund(fund_id):
        own = store.get_ownership(fund_id, deal.deal_id)
        cfs = store.get_cashflows(fund_id=fund_id, deal_id=deal.deal_id)
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
async def get_cashflows(fund_id: str, deal_id: str | None = None) -> dict:
    """Cashflow summary for a fund or specific deal."""
    cfs = store.get_cashflows(fund_id=fund_id, deal_id=deal_id)
    total_contribution = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
    total_disposition = sum(c.fund_amt for c in cfs if c.cf_type == "disposition")
    total_income = sum(c.fund_amt for c in cfs if c.cf_type == "income")
    records = sorted(
        [{"date": c.cash_date, "deal_id": c.deal_id, "type": c.cf_type,
          "amount": round(c.fund_amt, 4)} for c in cfs],
        key=lambda r: str(r["date"]),
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
    sector_data: dict = {}
    for fid in store.funds:
        for deal in store.get_deals_for_fund(fid):
            sec = deal.sector
            if sec not in sector_data:
                sector_data[sec] = {"total_invested": 0.0, "total_received": 0.0, "deal_count": 0}
            cfs = store.get_cashflows(fund_id=fid, deal_id=deal.deal_id)
            sector_data[sec]["total_invested"] += sum(
                abs(c.fund_amt) for c in cfs if c.cf_type == "contribution"
            )
            sector_data[sec]["total_received"] += sum(
                c.fund_amt for c in cfs if c.cf_type in ("disposition", "income")
            )
            sector_data[sec]["deal_count"] += 1
    for v in sector_data.values():
        v["total_invested"] = round(v["total_invested"], 4)
        v["total_received"] = round(v["total_received"], 4)
    return sector_data


@app.post("/api/run-agent")
async def run_agent(task_id: str = "easy") -> dict:
    """Run the baseline pass-through agent end-to-end on `demo_env`.

    Returns the full step log + grading result so the frontend can replay it
    without having to deal with the stateless OpenEnv HTTP /reset+/step lifecycle.
    """
    if task_id not in _LOADERS:
        return {"error": f"Unknown task_id '{task_id}'"}

    steps: list[dict] = []

    # Step 1: reset
    reset_obs = demo_env.reset(task_id=task_id)
    funds = list(reset_obs.available_funds)
    if not funds:
        return {"error": "No funds available after reset"}
    primary_fund = funds[0]

    steps.append({
        "n": 1,
        "action": "reset",
        "args": {"task_id": task_id},
        "result": {
            "available_funds": funds,
            "task_description": reset_obs.task_description,
            "difficulty": reset_obs.difficulty,
        },
    })

    # Step 2: get_nav_bridge for primary fund
    bridge_action = CallToolAction(
        tool_name="get_nav_bridge",
        arguments={"fund_id": primary_fund},
    )
    bridge_obs = demo_env.step(bridge_action)
    bridge = unwrap_tool_result(bridge_obs) or {}
    steps.append({
        "n": 2,
        "action": "get_nav_bridge",
        "args": {"fund_id": primary_fund},
        "result": bridge,
    })

    if "error" in bridge:
        return {"error": bridge["error"], "steps": steps}

    # Step 3 (medium/hard): get_portfolio_summary for metrics
    metrics: dict[str, float] | None = None
    if task_id in ("medium", "hard"):
        metrics_action = CallToolAction(
            tool_name="get_portfolio_summary",
            arguments={"funds": [primary_fund]},
        )
        metrics_obs = demo_env.step(metrics_action)
        metrics_data = unwrap_tool_result(metrics_obs) or {}
        fund_metrics = metrics_data.get(primary_fund, {}) if isinstance(metrics_data, dict) else {}
        metrics = {}
        if "moic" in fund_metrics:
            metrics["moic"] = fund_metrics["moic"]
        if task_id == "hard" and "irr" in fund_metrics:
            metrics["irr"] = fund_metrics["irr"]

        steps.append({
            "n": 3,
            "action": "get_portfolio_summary",
            "args": {"funds": [primary_fund]},
            "result": fund_metrics,
        })

    # Final step: submit_report
    submit_args: dict[str, Any] = {"nav_bridge": bridge}
    if metrics:
        submit_args["metrics"] = metrics

    submit_action = CallToolAction(tool_name="submit_report", arguments=submit_args)
    submit_obs = demo_env.step(submit_action)
    grading = unwrap_tool_result(submit_obs) or {}

    steps.append({
        "n": len(steps) + 1,
        "action": "submit_report",
        "args": {
            "bridge_items": len(bridge),
            "metrics": list(metrics.keys()) if metrics else [],
        },
        "result": grading,
    })

    return {
        "task_id": task_id,
        "primary_fund": primary_fund,
        "steps": steps,
        "grading": grading,
    }


# Serve React frontend (must be LAST -- catches all unmatched routes)
_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "frontend", "dist")
if os.path.isdir(_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    @app.get("/{path:path}")
    async def serve_frontend(path: str) -> FileResponse:
        """Serve React SPA -- all non-API routes go to index.html."""
        file_path = os.path.join(_DIST, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_DIST, "index.html"))

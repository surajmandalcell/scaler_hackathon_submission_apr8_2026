"""FastAPI application -- OpenEnv API + REST endpoints for React frontend."""
from __future__ import annotations

import os

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openenv.core.env_server import CallToolAction, create_app

from fundlens.models import FundLensObservation
from fundlens.server.calculations import compute_metrics, compute_nav_bridge
from fundlens.server.data_store import DataStore
from fundlens.server.environment import FundLensEnvironment
from fundlens.server.seed_data import load_easy_task, load_hard_task, load_medium_task

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
    """Health check for container orchestration / HuggingFace Space."""
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
async def get_cashflows(fund_id: str, deal_id: str | None = None) -> dict:
    """Cashflow summary for a fund or specific deal."""
    cfs = _api_store.get_cashflows(fund_id=fund_id, deal_id=deal_id)
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
    for fid in _api_store.funds:
        for deal in _api_store.get_deals_for_fund(fid):
            sec = deal.sector
            if sec not in sector_data:
                sector_data[sec] = {"total_invested": 0.0, "total_received": 0.0, "deal_count": 0}
            cfs = _api_store.get_cashflows(fund_id=fid, deal_id=deal.deal_id)
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

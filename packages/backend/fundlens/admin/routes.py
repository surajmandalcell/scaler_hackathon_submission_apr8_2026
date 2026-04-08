"""Admin REST routes -- /api/admin/*.

Data entry (fund/deal/ownership/cashflow CRUD), Excel template downloads, xlsx
bulk upload parsing, answer-key export, and a test-run route that wraps the
baseline agent and pairs its output with the computed correct answers so the
frontend can render a side-by-side comparison.

The admin router never mutates `demo_env` (the Playground session state). When
it needs the correct answers for a task it constructs a throwaway
`DataStore()`, runs the appropriate loader into it, and calls
`get_correct_answers` on that instance -- this keeps the Playground tab free
from being silently reset when the user clicks "Show answer key" in Admin.
"""
from __future__ import annotations

import os
import re
import tempfile
from typing import Any

from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from fundlens.admin.export import export_answer_key
from fundlens.admin.templates import (
    generate_cashflow_template,
    generate_onboarding_template,
    parse_cashflow_upload,
    parse_onboarding_upload,
)
from fundlens.models import Cashflow, Deal, Fund, Ownership
from fundlens.server.calculations import compute_metrics, compute_nav_bridge
from fundlens.server.data_store import DataStore, store
from fundlens.server.seed_data import (
    load_easy_task,
    load_hard_task,
    load_medium_task,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


LOADERS = {
    "easy": load_easy_task,
    "medium": load_medium_task,
    "hard": load_hard_task,
}


# ── Helpers ──────────────────────────────────────────────────────────────────


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


def _compute_correct_answers(task_id: str) -> dict[str, Any]:
    """Load `task_id` into a throwaway store and return the canonical answers.

    IMPORTANT: This intentionally does NOT mutate the shared `store` or
    `demo_env`. The Analyst tab and Playground tab keep whatever scenario the
    user is currently working with.
    """
    loader = LOADERS.get(task_id)
    if loader is None:
        return {}
    tmp = DataStore()
    loader(tmp)
    answers: dict[str, Any] = {}
    for fid, fund in tmp.funds.items():
        bridge = compute_nav_bridge(fid, tmp)
        metrics = compute_metrics(fid, tmp)
        answers[fid] = {
            "fund_name": fund.fund_name,
            "nav_bridge": {k: round(v, 4) for k, v in bridge.items()},
            "metrics": {k: round(v, 4) for k, v in metrics.items()},
        }
    return answers


def _next_cashflow_id(store_inst: DataStore, fund_id: str, deal_id: str) -> str:
    existing = store_inst.get_cashflows(fund_id=fund_id, deal_id=deal_id)
    return f"{deal_id}_{fund_id}_{len(existing) + 1}"


# ── Request models ───────────────────────────────────────────────────────────


class FundIn(BaseModel):
    fund_id: str | None = None  # auto-slugged from fund_name when omitted
    fund_name: str
    fund_currency: str = "USD"
    reporting_date: str = ""
    beginning_nav: float = 0.0
    ending_nav: float = 0.0
    nav_period_start: str = ""


class DealIn(BaseModel):
    deal_id: str | None = None
    property_name: str
    sector: str = "Other"
    location: str = ""
    appraiser_nav: float = 0.0


class OwnershipIn(BaseModel):
    fund_id: str
    deal_id: str
    ownership_pct: float = Field(ge=0.0, le=1.0)
    entry_date: str = ""


class CashflowIn(BaseModel):
    cashflow_id: str | None = None
    fund_id: str
    deal_id: str
    cash_date: str
    cf_type: str  # contribution | disposition | income
    fund_amt: float


# ── CRUD routes ──────────────────────────────────────────────────────────────


@router.post("/fund")
async def create_fund(payload: FundIn) -> dict[str, Any]:
    fund_id = payload.fund_id or _slug(payload.fund_name)
    if not fund_id:
        return {"error": "fund_id could not be derived from fund_name"}
    fund = Fund(
        fund_id=fund_id,
        fund_name=payload.fund_name,
        fund_currency=payload.fund_currency,
        reporting_date=payload.reporting_date,
        beginning_nav=payload.beginning_nav,
        ending_nav=payload.ending_nav,
        nav_period_start=payload.nav_period_start,
    )
    store.add_fund(fund)
    return {"ok": True, "fund_id": fund_id}


@router.post("/deal")
async def create_deal(payload: DealIn) -> dict[str, Any]:
    deal_id = payload.deal_id or _slug(payload.property_name)
    if not deal_id:
        return {"error": "deal_id could not be derived from property_name"}
    deal = Deal(
        deal_id=deal_id,
        property_name=payload.property_name,
        sector=payload.sector,
        location=payload.location,
        appraiser_nav=payload.appraiser_nav,
    )
    store.add_deal(deal)
    return {"ok": True, "deal_id": deal_id}


@router.post("/ownership")
async def create_ownership(payload: OwnershipIn) -> dict[str, Any]:
    if payload.fund_id not in store.funds:
        return {"error": f"fund '{payload.fund_id}' not found"}
    if payload.deal_id not in store.deals:
        return {"error": f"deal '{payload.deal_id}' not found"}
    own = Ownership(
        fund_id=payload.fund_id,
        deal_id=payload.deal_id,
        ownership_pct=payload.ownership_pct,
        entry_date=payload.entry_date,
    )
    store.add_ownership(own)
    return {"ok": True}


@router.post("/cashflow")
async def create_cashflow(payload: CashflowIn) -> dict[str, Any]:
    if payload.cf_type not in ("contribution", "disposition", "income"):
        return {"error": f"invalid cf_type '{payload.cf_type}'"}
    cashflow_id = payload.cashflow_id or _next_cashflow_id(
        store, payload.fund_id, payload.deal_id
    )
    cf = Cashflow(
        cashflow_id=cashflow_id,
        deal_id=payload.deal_id,
        fund_id=payload.fund_id,
        cash_date=payload.cash_date,
        cf_type=payload.cf_type,
        fund_amt=payload.fund_amt,
    )
    store.add_cashflow(cf)
    return {"ok": True, "cashflow_id": cashflow_id}


@router.post("/recompute")
async def recompute_navs() -> dict[str, Any]:
    """Recompute every fund's ending_nav from its deals' appraiser values."""
    store.sync_all_fund_navs()
    return {
        "ok": True,
        "funds": {fid: round(f.ending_nav, 4) for fid, f in store.funds.items()},
    }


@router.post("/clear")
async def clear_store() -> dict[str, Any]:
    store.clear()
    return {"ok": True}


# ── Template downloads ───────────────────────────────────────────────────────


@router.get("/template/onboarding")
async def download_onboarding_template() -> FileResponse:
    path = generate_onboarding_template()
    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        filename="fundlens_onboarding_template.xlsx",
    )


@router.get("/template/cashflow")
async def download_cashflow_template() -> FileResponse:
    path = generate_cashflow_template()
    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        filename="fundlens_cashflow_template.xlsx",
    )


# ── Bulk upload ──────────────────────────────────────────────────────────────


async def _persist_upload_to_temp(file: UploadFile) -> str:
    suffix = os.path.splitext(file.filename or "upload.xlsx")[1] or ".xlsx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as fh:
        fh.write(await file.read())
        return fh.name


@router.post("/upload/onboarding")
async def upload_onboarding(file: UploadFile) -> dict[str, Any]:
    filepath = await _persist_upload_to_temp(file)
    funds_data, invs_data, err = parse_onboarding_upload(filepath)
    if err:
        return {"error": err}

    funds_added = 0
    for fd in funds_data:
        fid = _slug(fd["name"])
        if not fid:
            continue
        store.add_fund(Fund(
            fund_id=fid,
            fund_name=fd["name"],
            reporting_date="",
            nav_period_start=fd.get("quarter", ""),
            beginning_nav=0.0,
            ending_nav=0.0,
        ))
        funds_added += 1

    deals_added = 0
    ownerships_added = 0
    skipped = 0
    for inv in invs_data:
        fund = next(
            (f for f in store.funds.values() if f.fund_name == inv["fund_name"]),
            None,
        )
        if not fund:
            skipped += 1
            continue
        did = _slug(inv["deal_name"])
        if not did:
            skipped += 1
            continue
        if did not in store.deals:
            store.add_deal(Deal(
                deal_id=did,
                property_name=inv["deal_name"],
                sector="Other",
                location="",
            ))
            deals_added += 1
        store.add_ownership(Ownership(
            fund_id=fund.fund_id,
            deal_id=did,
            ownership_pct=float(inv.get("ownership_pct", 100.0)) / 100.0,
            entry_date=inv.get("quarter", ""),
        ))
        ownerships_added += 1

    return {
        "funds_added": funds_added,
        "deals_added": deals_added,
        "ownerships_added": ownerships_added,
        "skipped": skipped,
    }


_TXN_TYPE_MAP = {
    "Investment": "contribution",
    "Current Income": "income",
    "Disposition": "disposition",
}


@router.post("/upload/cashflow")
async def upload_cashflow(file: UploadFile) -> dict[str, Any]:
    filepath = await _persist_upload_to_temp(file)
    cfs_data, err = parse_cashflow_upload(filepath)
    if err:
        return {"error": err}

    cfs_data.sort(key=lambda r: r.get("date", ""))
    added = 0
    skipped = 0
    for row in cfs_data:
        fund = next(
            (f for f in store.funds.values() if f.fund_name == row["fund_name"]),
            None,
        )
        if not fund:
            skipped += 1
            continue
        did = _slug(row["deal_name"])
        if not did:
            skipped += 1
            continue
        if did not in store.deals:
            store.add_deal(Deal(
                deal_id=did,
                property_name=row["deal_name"],
                sector="Other",
                location="",
            ))
        cf_type = _TXN_TYPE_MAP.get(row["txn_type"])
        if not cf_type:
            skipped += 1
            continue
        store.add_cashflow(Cashflow(
            cashflow_id=_next_cashflow_id(store, fund.fund_id, did),
            deal_id=did,
            fund_id=fund.fund_id,
            cash_date=row["date"],
            cf_type=cf_type,
            fund_amt=float(row["fund_amt"]),
        ))
        added += 1

    return {"cashflows_added": added, "skipped": skipped}


# ── Answer key ───────────────────────────────────────────────────────────────


@router.get("/answer-key")
async def download_answer_key() -> FileResponse:
    """Download the answer-key xlsx for the current shared store contents."""
    path = export_answer_key(store)
    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        filename="fundlens_answer_key.xlsx",
    )


@router.get("/answer-key/json")
async def answer_key_json(task_id: str = "easy") -> dict[str, Any]:
    """Canonical correct answers for a given task, computed in a throwaway store.

    Never mutates `store` or `demo_env` -- safe to call from the Admin tab
    while the user is running a session in the Playground tab.
    """
    answers = _compute_correct_answers(task_id)
    if not answers:
        return {"error": f"unknown task_id '{task_id}'"}
    return {"task_id": task_id, "answers": answers}


@router.post("/test-run")
async def test_run(task_id: str = "easy") -> dict[str, Any]:
    """Baseline test run with paired correct answers for side-by-side rendering.

    Mirrors the flow of the canned `/api/run-agent` route but also attaches
    the throwaway-store answers so the Admin tab can diff AI vs Correct per
    line item.
    """
    # Reuse the baseline runner directly -- imported lazily to avoid a
    # circular import between app.py and this module.
    from fundlens.server.app import run_agent

    result = await run_agent(task_id=task_id)
    answers = _compute_correct_answers(task_id)
    return {
        "task_id": task_id,
        "run": result,
        "correct_answers": answers,
    }



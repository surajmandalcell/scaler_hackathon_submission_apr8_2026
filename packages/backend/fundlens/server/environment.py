"""FundLens MCP Environment — tools + reset/step/state lifecycle."""
from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from openenv.core.env_server import MCPEnvironment

from fundlens.models import FundLensObservation, FundLensState
from fundlens.server.calculations import (
    compute_deal_metrics,
    compute_deal_nav_bridge,
    compute_metrics,
    compute_nav_bridge,
    compute_portfolio_metrics,
    compute_portfolio_nav_bridge,
)
from fundlens.server.data_store import DataStore
from fundlens.server.grader import grade_full_submission
from fundlens.server.seed_data import (
    TASK_DESCRIPTIONS,
    get_correct_answers,
    load_easy_task,
    load_hard_task,
    load_medium_task,
)

LOADERS = {
    "easy":   load_easy_task,
    "medium": load_medium_task,
    "hard":   load_hard_task,
}

# ── Cross-request state (HTTP /reset + /step) ────────────────────────────
#
# OpenEnv's REST server at env_server/http_server.py:582,617 instantiates
# a fresh FundLensEnvironment per request and calls close() afterwards.
# Any state we set on `self` during reset() is therefore invisible to the
# next /step call. We persist the two pieces of per-episode state that
# submit_report needs at module scope so they survive across requests:
#
#   - `_SESSION_TASK_ID`: which difficulty level reset() was called with,
#     needed by the grader to pick tolerance weights.
#
# Correct answers are NOT cached here -- they are pure-recomputed from the
# store inside submit_report (the store itself is shared via the factory
# in app.py), so they always match whatever scenario is currently loaded.
_SESSION_TASK_ID: str = ""


class FundLensEnvironment(MCPEnvironment):

    def __init__(self, store: DataStore | None = None) -> None:
        # When `store` is None (the default), create a private in-memory store
        # so that OpenEnv's stateless `/reset`/`/step` handlers -- which build
        # `FundLensEnvironment()` fresh per request and discard it afterwards
        # (openenv-core http_server.py:582,617) -- continue to work without
        # leaking data between requests.
        #
        # When an explicit `store` is injected (e.g. the SQLite-backed
        # module-level singleton from data_store.py), the env shares that
        # store with REST endpoints. This is how the long-lived `_demo_env`
        # used by the Playground stays consistent with the Analyst/Admin/
        # Investor views.
        self._store = store if store is not None else DataStore()
        self._state = FundLensState()
        self._correct_answers: dict = {}

        mcp = FastMCP("fundlens")

        # ── Tool 1: get_available_filters ──────────────────────────────────
        @mcp.tool()
        def get_available_filters() -> dict:
            """List valid fund_ids, deal_ids, sectors, and cashflow types."""
            return {
                "fund_ids":  list(self._store.funds.keys()),
                "deal_ids":  list(self._store.deals.keys()),
                "sectors":   sorted({d.sector for d in self._store.deals.values()}),
                "cf_types":  ["contribution", "disposition", "income"],
            }

        # ── Tool 2: get_portfolio_summary ──────────────────────────────────
        @mcp.tool()
        def get_portfolio_summary(funds: list[str] | None = None) -> dict:
            """Fund-level ending NAV, MOIC, and IRR for all or selected funds."""
            fund_ids = list(self._store.funds.keys()) if not funds else funds
            result = {}
            for fid in fund_ids:
                if fid not in self._store.funds:
                    continue
                fund = self._store.funds[fid]
                metrics = compute_metrics(fid, self._store)
                result[fid] = {
                    "fund_name":      fund.fund_name,
                    "reporting_date": fund.reporting_date,
                    "ending_nav":     round(fund.ending_nav, 4),
                    **{k: round(v, 4) for k, v in metrics.items()},
                }
            return result

        # ── Tool 3: get_nav_bridge ─────────────────────────────────────────
        @mcp.tool()
        def get_nav_bridge(fund_id: str) -> dict:
            """8-line NAV bridge for a fund (USD millions).
            Lines: beginning_nav, contribution, disposition, income,
                   cashflow_adjusted_nav, income_reversal, write_up_down, ending_nav."""
            bridge = compute_nav_bridge(fund_id, self._store)
            if not bridge:
                return {"error": f"Fund '{fund_id}' not found"}
            return {k: round(v, 4) for k, v in bridge.items()}

        # ── Tool 4: get_irr ────────────────────────────────────────────────
        @mcp.tool()
        def get_irr(fund_id: str) -> dict:
            """IRR (USD, all historical cashflows + terminal ending NAV)."""
            metrics = compute_metrics(fund_id, self._store)
            if not metrics:
                return {"error": f"Fund '{fund_id}' not found"}
            return {"irr": round(metrics["irr"], 4)}

        # ── Tool 5: compare_funds ──────────────────────────────────────────
        @mcp.tool()
        def compare_funds(
            funds: list[str] | None = None,
            metrics: list[str] | None = None,
        ) -> dict:
            """Side-by-side comparison. metrics options: moic | irr | ending_nav."""
            fund_ids = list(self._store.funds.keys()) if not funds else funds
            keys = metrics or ["moic", "irr", "ending_nav"]
            result = {}
            for fid in fund_ids:
                if fid not in self._store.funds:
                    continue
                m = compute_metrics(fid, self._store)
                fund = self._store.funds[fid]
                row: dict[str, Any] = {"fund_name": fund.fund_name}
                for k in keys:
                    if k == "ending_nav":
                        row[k] = round(fund.ending_nav, 4)
                    elif k in m:
                        row[k] = round(m[k], 4)
                result[fid] = row
            return result

        # ── Tool 6: get_sector_report ──────────────────────────────────────
        @mcp.tool()
        def get_sector_report(
            sector: str | None = None,
            funds: list[str] | None = None,
        ) -> dict:
            """Invested capital and distributions grouped by property sector."""
            fund_ids = list(self._store.funds.keys()) if not funds else funds
            sector_data: dict[str, dict] = {}

            for fid in fund_ids:
                for deal in self._store.get_deals_for_fund(fid):
                    if sector and deal.sector != sector:
                        continue
                    sec = deal.sector
                    if sec not in sector_data:
                        sector_data[sec] = {
                            "total_invested": 0.0,
                            "total_received": 0.0,
                            "deal_count": 0,
                            "deals": [],
                        }
                    cfs = self._store.get_cashflows(fund_id=fid, deal_id=deal.deal_id)
                    invested = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
                    received = sum(c.fund_amt for c in cfs if c.cf_type in ("disposition", "income"))
                    own = self._store.get_ownership(fid, deal.deal_id)
                    sector_data[sec]["total_invested"] += invested
                    sector_data[sec]["total_received"] += received
                    sector_data[sec]["deal_count"] += 1
                    sector_data[sec]["deals"].append({
                        "deal_id":       deal.deal_id,
                        "fund_id":       fid,
                        "ownership_pct": own.ownership_pct if own else 1.0,
                        "property_name": deal.property_name,
                        "location":      deal.location,
                    })

            for data in sector_data.values():
                data["total_invested"] = round(data["total_invested"], 4)
                data["total_received"] = round(data["total_received"], 4)

            return sector_data

        # ── Tool 7: get_deal_exposure ──────────────────────────────────────
        @mcp.tool()
        def get_deal_exposure(deal_id: str) -> dict:
            """Deal shown across all funds that hold it, with per-fund ownership and cashflows."""
            if deal_id not in self._store.deals:
                return {"error": f"Deal '{deal_id}' not found"}

            deal = self._store.deals[deal_id]
            fund_ids = self._store.get_funds_for_deal(deal_id)
            per_fund: dict[str, Any] = {}
            total_ownership = 0.0
            total_invested = 0.0
            total_received = 0.0

            for fid in fund_ids:
                own = self._store.get_ownership(fid, deal_id)
                if not own:
                    continue
                cfs = self._store.get_cashflows(fund_id=fid, deal_id=deal_id)
                invested = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
                received = sum(c.fund_amt for c in cfs if c.cf_type in ("disposition", "income"))
                per_fund[fid] = {
                    "ownership_pct":       own.ownership_pct,
                    "total_invested_usd":  round(invested, 4),
                    "total_received_usd":  round(received, 4),
                }
                total_ownership += own.ownership_pct
                total_invested  += invested
                total_received  += received

            return {
                "deal_id":       deal_id,
                "property_name": deal.property_name,
                "sector":        deal.sector,
                "per_fund":      per_fund,
                "consolidated": {
                    "total_ownership_pct": round(total_ownership, 4),
                    "total_invested_usd":  round(total_invested, 4),
                    "total_received_usd":  round(total_received, 4),
                },
            }

        # ── Tool 8: get_raw_cashflows ─────────────────────────────────────
        @mcp.tool()
        def get_raw_cashflows(
            fund_id: str,
            deal_id: str | None = None,
            limit: int = 200,
            offset: int = 0,
        ) -> dict:
            """Individual cashflow records — paginated for large datasets.
            Use limit/offset to page through: offset=0 first, then offset+=limit.
            cf_type: contribution (negative = capital out),
                     disposition (positive = sale proceeds),
                     income (positive = rent/yield).
            TIP: For computation use get_cashflow_summary — it returns pre-aggregated
            totals regardless of row count and is always faster."""
            cfs = self._store.get_cashflows(fund_id=fund_id, deal_id=deal_id)
            if not cfs:
                return {"error": f"No cashflows for fund='{fund_id}'" +
                        (f" deal='{deal_id}'" if deal_id else "")}
            sorted_cfs = sorted(cfs, key=lambda c: c.cash_date)
            total = len(sorted_cfs)
            page  = sorted_cfs[offset: offset + limit]
            records = [
                {
                    "date":         c.cash_date,
                    "deal_id":      c.deal_id,
                    "type":         c.cf_type,
                    "amount_usd_m": round(c.fund_amt, 4),
                }
                for c in page
            ]
            return {
                "fund_id":    fund_id,
                "deal_id":    deal_id,
                "total":      total,
                "offset":     offset,
                "limit":      limit,
                "has_more":   (offset + limit) < total,
                "records":    records,
            }

        # ── Tool 8b: get_cashflow_summary ─────────────────────────────────
        @mcp.tool()
        def get_cashflow_summary(
            fund_id: str,
            deal_id: str | None = None,
        ) -> dict:
            """Pre-aggregated cashflow summary — scales to any dataset size.
            Returns totals by type + a dated IRR schedule (one net row per date).
            Use this for NAV bridge computation and MOIC/IRR — NOT raw rows.

            irr_schedule: list of {date, net_amount} where contributions are
            negative and distributions (disposition+income) are positive.
            Pass this schedule directly to an XIRR solver."""
            cfs = self._store.get_cashflows(fund_id=fund_id, deal_id=deal_id)
            if not cfs:
                return {"error": f"No cashflows for fund='{fund_id}'" +
                        (f" deal='{deal_id}'" if deal_id else "")}

            total_contribution = 0.0
            total_disposition  = 0.0
            total_income       = 0.0
            irr_by_date: dict[str, float] = {}

            for c in cfs:
                if c.cf_type == "contribution":
                    total_contribution += abs(c.fund_amt)   # positive display
                    irr_by_date[c.cash_date] = irr_by_date.get(c.cash_date, 0.0) + c.fund_amt  # negative
                elif c.cf_type == "disposition":
                    total_disposition += c.fund_amt
                    irr_by_date[c.cash_date] = irr_by_date.get(c.cash_date, 0.0) + c.fund_amt
                elif c.cf_type == "income":
                    total_income += c.fund_amt
                    irr_by_date[c.cash_date] = irr_by_date.get(c.cash_date, 0.0) + c.fund_amt

            irr_schedule = [
                {"date": d, "net_amount": round(v, 4)}
                for d, v in sorted(irr_by_date.items())
            ]

            return {
                "fund_id":            fund_id,
                "deal_id":            deal_id,
                "source_row_count":   len(cfs),
                "total_contribution": round(total_contribution, 4),  # positive
                "total_disposition":  round(total_disposition, 4),
                "total_income":       round(total_income, 4),
                "irr_schedule":       irr_schedule,
                "note": (
                    "Use total_contribution as 'contribution' in NAV bridge. "
                    "For IRR: append {date: reporting_date, net_amount: ending_nav} "
                    "to irr_schedule, then compute XIRR."
                ),
            }

        # ── Tool 9: get_deal_info ──────────────────────────────────────────
        @mcp.tool()
        def get_deal_info(fund_id: str) -> dict:
            """Property-level data for all deals in a fund.
            Returns sector, location, ownership_pct, and current appraiser_nav
            (the authoritative ending value from the property appraiser).
            ending_nav for the fund = sum(appraiser_nav × ownership_pct) across all deals."""
            if fund_id not in self._store.funds:
                return {"error": f"Fund '{fund_id}' not found"}
            fund = self._store.funds[fund_id]
            deals_out = {}
            for deal in self._store.get_deals_for_fund(fund_id):
                own = self._store.get_ownership(fund_id, deal.deal_id)
                deals_out[deal.deal_id] = {
                    "property_name":  deal.property_name,
                    "sector":         deal.sector,
                    "location":       deal.location,
                    "ownership_pct":  own.ownership_pct if own else 1.0,
                    "appraiser_nav":  round(deal.appraiser_nav, 4),
                    "fund_share_nav": round(deal.appraiser_nav * (own.ownership_pct if own else 1.0), 4),
                }
            fund_ending_nav: float = sum(d["fund_share_nav"] for d in deals_out.values())  # type: ignore[misc]
            # Add deal-level beginning_nav (proportional allocation of fund beginning_nav)
            for d in deals_out.values():
                if fund_ending_nav > 0:
                    share: float = d["fund_share_nav"]  # type: ignore[assignment]
                    d["deal_beginning_nav"] = round(
                        fund.beginning_nav * (share / fund_ending_nav), 4
                    )
                else:
                    d["deal_beginning_nav"] = 0.0
            return {
                "fund_id":            fund_id,
                "fund_name":          fund.fund_name,
                "fund_beginning_nav": round(fund.beginning_nav, 4),
                "reporting_date":     fund.reporting_date,
                "deals":              deals_out,
                "total_ending_nav":   round(fund_ending_nav, 4),
                "note": "Use deal_beginning_nav (not fund_beginning_nav) when computing a single deal's NAV bridge.",
            }

        # ── Tool 10: get_portfolio_bridge ─────────────────────────────────
        @mcp.tool()
        def get_portfolio_bridge() -> dict:
            """8-line NAV bridge aggregated across ALL funds (portfolio level, USD millions)."""
            bridge = compute_portfolio_nav_bridge(self._store)
            if not bridge:
                return {"error": "No funds loaded"}
            return {k: round(v, 4) for k, v in bridge.items()}

        # ── Tool 11: get_deal_bridge ───────────────────────────────────────
        @mcp.tool()
        def get_deal_bridge(fund_id: str, deal_id: str) -> dict:
            """8-line NAV bridge for a single deal within a fund.
            beginning_nav is proportionally estimated from fund beginning_nav."""
            bridge = compute_deal_nav_bridge(fund_id, deal_id, self._store)
            if not bridge:
                return {"error": f"Fund '{fund_id}' or deal '{deal_id}' not found"}
            return {k: round(v, 4) for k, v in bridge.items()}

        # ── Tool 12: get_deal_metrics ──────────────────────────────────────
        @mcp.tool()
        def get_deal_metrics(fund_id: str, deal_id: str) -> dict:
            """MOIC and IRR for a single deal within a fund."""
            m = compute_deal_metrics(fund_id, deal_id, self._store)
            if not m:
                return {"error": f"Fund '{fund_id}' or deal '{deal_id}' not found or no invested capital"}
            return {k: round(v, 4) for k, v in m.items()}

        # ── Tool 13: get_portfolio_metrics ─────────────────────────────────
        @mcp.tool()
        def get_portfolio_metrics() -> dict:
            """MOIC and IRR pooled across ALL funds (portfolio level)."""
            m = compute_portfolio_metrics(self._store)
            if not m:
                return {"error": "No funds loaded or no invested capital"}
            return {k: round(v, 4) for k, v in m.items()}

        # ── Tool 14: submit_report ─────────────────────────────────────────
        @mcp.tool()
        def submit_report(
            nav_bridge: dict[str, float],
            metrics: dict[str, float] | None = None,
        ) -> dict:
            """Grade submission. Returns reward 0.0–1.0.
            easy:   nav_bridge only
            medium: nav_bridge + metrics={"moic": value}
            hard:   nav_bridge + metrics={"moic": value, "irr": value}
            """
            # Recompute correct answers from the *current* store state so
            # stateless /reset + /step flows (where this env instance was
            # created fresh for just this step) still see the right data.
            correct_answers = self._correct_answers or get_correct_answers(self._store)
            fund_ids = list(self._store.funds.keys())
            primary = fund_ids[0] if fund_ids else "alpha"
            correct_bridge  = correct_answers.get(f"nav_bridge_{primary}", {})
            correct_metrics = correct_answers.get(f"metrics_{primary}", {})
            # task_id: prefer instance state (tests & playground), fall back
            # to the module-level session id set by the most recent reset()
            # when this instance was built by the REST factory.
            task_id = self._state.task_id or _SESSION_TASK_ID

            grading = grade_full_submission(
                nav_bridge=nav_bridge,
                metrics=metrics,
                correct_bridge=correct_bridge,
                correct_metrics=correct_metrics,
                task_id=task_id,
            )
            self._state.is_done = True

            return {
                "reward":             grading["reward"],
                "task_id":            task_id,
                "bridge_reward":      grading["bridge_reward"],
                "metrics_reward":     grading["metrics_reward"],
                "bridge_score":       grading["bridge_score"],
                "metrics_score":      grading["metrics_score"],
                "correct_nav_bridge": correct_bridge,
                "correct_metrics":    correct_metrics,
                "message":            f"Episode complete. Reward: {grading['reward']:.4f}",
            }

        super().__init__(mcp)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        task_id: str = "easy",
        **kwargs,
    ) -> FundLensObservation:
        loader = LOADERS.get(task_id, load_easy_task)
        loader(self._store)
        self._correct_answers = get_correct_answers(self._store)
        self._state = FundLensState(task_id=task_id, is_done=False)
        # Publish the task_id at module scope so the very next /step
        # request -- which arrives on a brand-new env instance built by
        # the REST factory -- can still tell the grader which weights to
        # use. Harmless no-op for tests / playground (they see the
        # instance-level `_state.task_id` first).
        global _SESSION_TASK_ID
        _SESSION_TASK_ID = task_id

        total_nav = sum(f.ending_nav for f in self._store.funds.values())

        level_instructions = {
            "easy": (
                "LEVEL 1 — NAV BRIDGE ONLY. "
                "Call get_nav_bridge(fund_id) to get cashflow data. "
                "Compute the 8-line bridge and submit_report(nav_bridge={...})."
            ),
            "medium": (
                "LEVEL 2 — NAV BRIDGE + MOIC. "
                "Compute the bridge and MOIC. "
                "submit_report(nav_bridge={...}, metrics={\"moic\": value})."
            ),
            "hard": (
                "LEVEL 3 — NAV BRIDGE + MOIC + IRR. "
                "Compute the bridge, MOIC, and IRR. "
                "submit_report(nav_bridge={...}, metrics={\"moic\": value, \"irr\": value})."
            ),
        }

        return FundLensObservation(
            task_id=task_id,
            difficulty=task_id,
            task_description=TASK_DESCRIPTIONS.get(task_id, ""),
            available_funds=list(self._store.funds.keys()),
            reporting_period="Q4_2024",
            portfolio_nav_usd=round(total_nav, 2),
            message=level_instructions.get(task_id, level_instructions["easy"]),
        )

    def _step_impl(self, action, **kwargs):
        return FundLensObservation(
            message=f"Unknown action type: {type(action).__name__}",
        )

    @property
    def state(self) -> FundLensState:
        return self._state

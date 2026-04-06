"""Pydantic data models for FundLens."""
from __future__ import annotations
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from openenv.core.env_server import Observation, State, Action


# ── Domain models ──────────────────────────────────────────────────────────

class Fund(BaseModel):
    fund_id: str
    fund_name: str
    fund_currency: str = "USD"
    reporting_date: str              # "YYYY-MM-DD"
    beginning_nav: float             # USD millions
    ending_nav: float                # USD millions — appraiser value; plug derived from this
    nav_period_start: str = ""       # "YYYY-MM-DD" — cashflows on/after go into NAV bridge


class Deal(BaseModel):
    deal_id: str
    property_name: str
    sector: str                      # Office | Residential | Logistics | Data Center
    location: str
    appraiser_nav: float = 0.0       # 100% property value (appraiser). Fund share = appraiser_nav × ownership_pct


class Ownership(BaseModel):
    deal_id: str
    fund_id: str
    ownership_pct: float             # 0.0 – 1.0
    entry_date: str                  # "YYYY-MM-DD"


class Cashflow(BaseModel):
    cashflow_id: str
    deal_id: str
    fund_id: str
    cash_date: str                   # "YYYY-MM-DD"
    cf_type: str                     # contribution | disposition | income
    fund_amt: float                  # USD millions
                                     # contribution = negative (outflow)
                                     # disposition  = positive (proceeds received)
                                     # income       = positive (inflow)


# ── OpenEnv models ─────────────────────────────────────────────────────────

class FundLensObservation(Observation):
    task_id: str = ""
    difficulty: str = ""
    task_description: str = ""
    available_funds: List[str] = Field(default_factory=list)
    reporting_period: str = ""
    portfolio_nav_usd: float = 0.0
    tool_result: Optional[Any] = None
    grading_result: Optional[Dict] = None
    message: str = ""


class FundLensState(State):
    task_id: str = ""
    max_steps: int = 10
    is_done: bool = False


class FundLensAction(Action):
    """Thin wrapper — MCP tool calls handled via CallToolAction."""
    pass

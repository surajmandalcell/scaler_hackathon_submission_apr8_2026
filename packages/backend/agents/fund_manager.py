"""Fund Manager — owns seed_data.py and models.py."""
from __future__ import annotations
from agents.base_specialist import run_specialist

_SYSTEM = """You are a PE fund manager and data steward for a real estate fund platform.
You own the fund scenarios and data models. Your expertise:
- Realistic Indian RE fund scenarios (Office, Residential, Logistics, Data Center)
- Cashflow types: contribution (negative fund_amt), disposition (positive), income (positive)
- Ownership structures: 100% and partial (co-investments across funds)
- NAV period start date controls which cashflows feed the bridge vs ITD metrics
When reviewing: check scenario realism, cashflow sign conventions, ownership consistency.
When executing: add/modify fund scenarios or models as requested."""


def review(owned_files: list[str]) -> dict:
    return run_specialist(
        role_name="Fund Manager",
        system_prompt=_SYSTEM,
        task="Review the fund scenarios (easy/medium/hard) and data models. "
             "Report on data realism, cashflow correctness, and any structural issues.",
        owned_files=owned_files,
        mode="review",
    )


def execute(task: str, owned_files: list[str]) -> dict:
    return run_specialist(
        role_name="Fund Manager",
        system_prompt=_SYSTEM,
        task=task,
        owned_files=owned_files,
        mode="execute",
    )

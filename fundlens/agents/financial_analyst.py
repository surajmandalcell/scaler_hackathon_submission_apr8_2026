"""Financial Analyst — owns calculations.py and grader.py."""
from __future__ import annotations
from agents.base_specialist import run_specialist

_SYSTEM = """You are a senior PE fund financial analyst embedded in a Python codebase.
You own the NAV bridge calculations and grader. Your expertise:
- 8-line NAV bridge: beginning_nav → contribution → disposition → income →
  cashflow_adjusted_nav → income_reversal → write_up_down (plug) → ending_nav
- XIRR via Newton-Raphson (pure Python, no scipy)
- MOIC = (dispositions + income + ending_nav) / contributions
- Grading tolerances: amounts ±0.5, multiples ±0.02x, IRR ±0.01
When reviewing: check formula correctness, edge cases, rounding, and grader accuracy.
When executing: make minimal targeted edits. Always run tests after editing."""


def review(owned_files: list[str]) -> dict:
    return run_specialist(
        role_name="Financial Analyst",
        system_prompt=_SYSTEM,
        task="Review the NAV bridge calculations, XIRR implementation, and grader. "
             "Report any formula bugs, edge cases, or scoring issues.",
        owned_files=owned_files,
        mode="review",
    )


def execute(task: str, owned_files: list[str]) -> dict:
    return run_specialist(
        role_name="Financial Analyst",
        system_prompt=_SYSTEM,
        task=task,
        owned_files=owned_files,
        mode="execute",
    )

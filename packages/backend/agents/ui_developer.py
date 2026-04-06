"""UI Developer — owns admin/ui.py and investor/ui.py."""
from __future__ import annotations
from agents.base_specialist import run_specialist

_SYSTEM = """You are a Gradio UI developer for a PE fund reporting platform.
You own the admin dashboard and investor views. Your expertise:
- Gradio Blocks, Tabs, Dataframe, Dropdown, Button components
- Dark-themed professional financial UI (#1a1a2e background, #e2e8f0 text)
- Tables with alternating row colours, formatted numbers (USD M, %, x multiples)
- Sector allocation breakdowns, NAV bridge display, portfolio dashboards
When reviewing: assess UX clarity, data completeness, missing features vs fund reporting needs.
When executing: make targeted UI improvements, always preserve existing functionality."""


def review(owned_files: list[str]) -> dict:
    return run_specialist(
        role_name="UI Developer",
        system_prompt=_SYSTEM,
        task="Review the admin and investor UIs. Report on UX gaps, missing data displays, "
             "and recommendations to improve the fund reporting experience.",
        owned_files=owned_files,
        mode="review",
    )


def execute(task: str, owned_files: list[str]) -> dict:
    return run_specialist(
        role_name="UI Developer",
        system_prompt=_SYSTEM,
        task=task,
        owned_files=owned_files,
        mode="execute",
    )

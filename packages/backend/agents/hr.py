"""
HR Agent — routing table, zero LLM calls.
Maps CEO category → specialist name + list of files the specialist owns.
"""
from __future__ import annotations

# category → (specialist_key, owned_files)
_ROUTING: dict[str, tuple[str, list[str]]] = {
    "finance": ("financial_analyst", [
        "fundlens/server/calculations.py",
        "fundlens/server/grader.py",
        "tests/test_calculations.py",
        "tests/test_grader.py",
    ]),
    "data": ("fund_manager", [
        "fundlens/server/seed_data.py",
        "fundlens/models.py",
        "fundlens/server/data_store.py",
    ]),
    "ui": ("ui_developer", [
        "fundlens/admin/ui.py",
        "fundlens/investor/ui.py",
        "fundlens/admin/templates.py",
        "fundlens/admin/export.py",
    ]),
    "infra": ("it_head", [
        "fundlens/server/app.py",
        "inference.py",
        "fundlens/server/environment.py",
        "requirements.txt",
    ]),
    "qa": ("qa_agent", [
        "tests/test_calculations.py",
        "tests/test_grader.py",
        "tests/test_environment.py",
    ]),
    "general": ("financial_analyst", [   # default fallback
        "fundlens/server/calculations.py",
    ]),
}


def route(ceo_output: dict) -> dict:
    """
    Returns {
        "specialist": str,
        "owned_files": list[str],
        "category": str,
        "priority": str,
        "task": str,
    }
    """
    category = ceo_output.get("category", "general")
    specialist, owned_files = _ROUTING.get(category, _ROUTING["general"])
    return {
        "specialist": specialist,
        "owned_files": owned_files,
        "category": category,
        "priority": ceo_output.get("priority", "medium"),
        "task": ceo_output.get("task", ""),
    }

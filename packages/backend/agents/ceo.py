"""
CEO Agent — pure Python keyword classifier, zero LLM calls.
Categorises a user request into one of 5 buckets and sets priority.
"""
from __future__ import annotations

# keyword → category mapping (checked in order, first match wins)
_RULES: list[tuple[list[str], str]] = [
    (["calculat", "xirr", "irr", "nav bridge", "moic", "grader", "grade",
      "metric", "dpi", "rvpi", "tvpi", "formula", "reconcil"], "finance"),
    (["seed", "fund data", "scenario", "deal data", "cashflow data",
      "model", "property data", "add fund", "add deal", "investment data"], "data"),
    (["ui", "dashboard", "gradio", "table", "chart", "display", "layout",
      "frontend", "visual", "sector chart", "colour", "color", "tab"], "ui"),
    (["docker", "server", "app.py", "fastapi", "inference", "deploy",
      "requirements", "port", "endpoint", "huggingface", "hf space"], "infra"),
    (["test", "bug", "fix", "error", "fail", "broken", "issue",
      "qa", "quality", "review", "check", "audit"], "qa"),
]

_PRIORITY_WORDS = {
    "high": ["urgent", "asap", "critical", "broken", "fail", "error", "bug"],
    "low":  ["minor", "nice to have", "eventually", "maybe", "consider"],
}


def classify(request: str) -> dict:
    """
    Returns {"category": str, "priority": str, "task": str}.
    category: finance | data | ui | infra | qa | general
    priority: high | medium | low
    """
    text = request.lower()

    category = "general"
    for keywords, cat in _RULES:
        if any(kw in text for kw in keywords):
            category = cat
            break

    priority = "medium"
    for level, words in _PRIORITY_WORDS.items():
        if any(w in text for w in words):
            priority = level
            break

    return {"category": category, "priority": priority, "task": request.strip()}

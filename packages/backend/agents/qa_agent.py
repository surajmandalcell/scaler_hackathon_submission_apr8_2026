"""
QA Agent — runs pytest first; uses claude -p (Claude Code CLI) only if tests fail.
Loops up to MAX_RETRIES times attempting auto-fix.
No Anthropic API key needed — runs on Claude Pro CLI session.
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from agents._tools import run_tests

MAX_RETRIES = 3
ROOT = Path(__file__).parent.parent

_SYSTEM = (
    "You are a QA engineer fixing pytest failures in a PE fund calculation codebase. "
    "Given a test failure output, identify the root cause and make the minimal fix. "
    "Use Read to inspect failing code, Edit to apply fixes. "
    "Fix only what the test output says is broken — do not refactor unrelated code."
)


def _claude_fix(failure_output: str, context: str, attempt: int) -> None:
    """Ask Claude CLI to fix the failing tests."""
    prompt = (
        f"{_SYSTEM}\n\n"
        f"pytest failed (attempt {attempt}/{MAX_RETRIES}):\n\n"
        f"{failure_output[:2000]}\n\n"
        f"Context: {context}\n\n"
        "Read the relevant source files and apply a minimal targeted fix."
    )
    subprocess.run(
        ["claude", "-p", prompt, "--allowedTools", "Read,Edit,Write,Bash,Glob,Grep"],
        cwd=str(ROOT),
        encoding="utf-8",
    )


def run_qa(context: str = "") -> dict:
    """
    Run QA pipeline.
    Returns {"passed": bool, "retries": int, "final_output": str, "fixes_applied": int}
    """
    passed, output = run_tests()
    if passed:
        return {"passed": True, "retries": 0, "final_output": output, "fixes_applied": 0}

    fixes_applied = 0
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  [QA] Tests failing — running fix attempt {attempt}/{MAX_RETRIES}...")
        _claude_fix(output, context, attempt)
        fixes_applied += 1
        passed, output = run_tests()
        if passed:
            return {
                "passed": True,
                "retries": attempt,
                "final_output": output,
                "fixes_applied": fixes_applied,
            }

    return {
        "passed": False,
        "retries": MAX_RETRIES,
        "final_output": output,
        "fixes_applied": fixes_applied,
    }

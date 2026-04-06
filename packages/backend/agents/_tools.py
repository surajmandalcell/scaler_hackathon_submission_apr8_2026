"""Shared file I/O and test runner used by all specialist agents."""
from __future__ import annotations
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent  # repo root


def read_file(path: str) -> str:
    """Read a file relative to repo root. Returns content or error string."""
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"ERROR: file not found: {path}"


def write_file(path: str, content: str) -> str:
    """Write content to path (relative to repo root). Returns status string."""
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"OK: wrote {len(content)} chars to {path}"


def run_tests() -> tuple[bool, str]:
    """Run pytest on tests/. Returns (passed: bool, output: str)."""
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    output = result.stdout + result.stderr
    passed = result.returncode == 0
    return passed, output

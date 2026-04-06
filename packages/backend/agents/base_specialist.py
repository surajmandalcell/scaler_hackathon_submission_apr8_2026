"""
Base specialist — uses Claude Code CLI (`claude -p`) via subprocess.
No Anthropic API key needed — runs on Claude Pro CLI session.

Supports two modes:
  review  — read owned files, return findings (no edits)
  execute — read + edit files to complete the task
"""
from __future__ import annotations
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent


def run_specialist(
    role_name: str,
    system_prompt: str,
    task: str,
    owned_files: list[str],
    mode: str = "review",   # "review" | "execute"
) -> dict:
    """
    Spawns a claude -p subprocess with the specialist's system prompt + task.
    Returns {"role": str, "mode": str, "findings": str, "files_edited": list[str]}
    """
    file_listing = "\n".join(f"- {f}" for f in owned_files)

    if mode == "review":
        mode_instruction = (
            "REVIEW MODE: Read your owned files using the Read tool. "
            "Do NOT edit any files. "
            "Produce a structured report with these sections:\n"
            "## Summary\n"
            "## Issues Found\n"
            "## Recommendations\n"
        )
        allowed_tools = "Read,Glob,Grep"
    else:
        mode_instruction = (
            "EXECUTE MODE: Complete the task by reading then editing the relevant files. "
            "Use the Read tool first, then Edit or Write to apply changes. "
            "Run tests with Bash after editing: `python -m pytest tests/ -q --tb=short`"
        )
        allowed_tools = "Read,Edit,Write,Bash,Glob,Grep"

    full_prompt = (
        f"{system_prompt}\n\n"
        f"---\n"
        f"Task: {task}\n\n"
        f"Your owned files (relative to repo root):\n{file_listing}\n\n"
        f"{mode_instruction}"
    )

    result = subprocess.run(
        ["claude", "-p", full_prompt, "--allowedTools", allowed_tools],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(ROOT),
    )

    findings = result.stdout.strip()
    if result.returncode != 0 and result.stderr:
        findings += f"\n\n[stderr]: {result.stderr[:300]}"

    # In execute mode, try to detect which files were mentioned as edited
    files_edited: list[str] = []
    if mode == "execute":
        for f in owned_files:
            if f in findings or Path(f).name in findings:
                files_edited.append(f)

    return {
        "role": role_name,
        "mode": mode,
        "findings": findings,
        "files_edited": files_edited,
    }

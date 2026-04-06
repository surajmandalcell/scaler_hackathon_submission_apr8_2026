"""
FundLens Agent Company — entry point.

Usage:
  python agents/run.py                         # review mode: all specialists audit the codebase
  python agents/run.py "your task here"        # execute mode: route task to right specialist
  python agents/run.py --review                # force review mode explicitly

Examples:
  python agents/run.py "fix the XIRR calculation"
  python agents/run.py "add a sector pie chart to the admin dashboard"
  python agents/run.py "add a new hard fund scenario with 8 properties"
  python agents/run.py "check Docker deployment config"
"""
from __future__ import annotations
import sys
from agents.ceo import classify
from agents.hr import route, _ROUTING
import agents.financial_analyst as financial_analyst
import agents.fund_manager as fund_manager
import agents.ui_developer as ui_developer
import agents.it_head as it_head
from agents.qa_agent import run_qa

_SPECIALISTS = {
    "financial_analyst": financial_analyst,
    "fund_manager":       fund_manager,
    "ui_developer":       ui_developer,
    "it_head":            it_head,
}


def _print_section(title: str) -> None:
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


def run_review() -> None:
    """All 4 specialists read their files and report findings. No edits made."""
    _print_section("REVIEW MODE — Full Company Audit")
    print("  Each specialist will read their owned files and report findings.")
    print("  No code will be changed in this mode.\n")

    all_results = []
    seen = set()

    for category, (specialist_key, owned_files) in _ROUTING.items():
        if specialist_key in ("qa_agent",) or specialist_key not in _SPECIALISTS:
            continue
        if specialist_key in seen:
            continue
        seen.add(specialist_key)

        mod = _SPECIALISTS[specialist_key]
        label = specialist_key.upper().replace("_", " ")
        print(f"[{label}]  reviewing {len(owned_files)} file(s)...")
        result = mod.review(owned_files)
        all_results.append(result)
        print(f"\n{result['findings']}\n")

    _print_section("QA — Running Tests")
    qa = run_qa()
    status = "✓ PASSED" if qa["passed"] else f"✗ FAILED after {qa['retries']} fix attempt(s)"
    print(f"  pytest: {status}")
    if not qa["passed"]:
        print(qa["final_output"][:800])

    _print_section("AUDIT COMPLETE")
    for r in all_results:
        print(f"  [{r['role']:<20}]  mode={r['mode']}")
    print(f"  [{'QA':<20}]  tests={'passed' if qa['passed'] else 'failed'}")


def run_task(request: str) -> None:
    """Route a task to the right specialist then run QA."""
    ceo_out = classify(request)
    hr_out  = route(ceo_out)

    _print_section(f"EXECUTE — {request[:55]}")
    print(f"  [CEO]  category={ceo_out['category']}  priority={ceo_out['priority']}")
    print(f"  [HR]   routing to → {hr_out['specialist']}")

    specialist_key = hr_out["specialist"]
    owned_files    = hr_out["owned_files"]

    if specialist_key == "qa_agent":
        print(f"\n[QA]  Running tests directly...")
        qa = run_qa(context=request)
        status = "✓ PASSED" if qa["passed"] else f"✗ FAILED after {qa['retries']} retries"
        print(f"  pytest: {status}")
        if qa["fixes_applied"]:
            print(f"  fixes applied to: {qa['fixes_applied']}")
        return

    mod = _SPECIALISTS.get(specialist_key)
    if not mod:
        print(f"  [ERROR] Unknown specialist: {specialist_key}")
        return

    label = specialist_key.upper().replace("_", " ")
    print(f"\n[{label}]  executing task...")
    result = mod.execute(request, owned_files)
    print(result["findings"])

    if result["files_edited"]:
        print(f"\n  Files edited: {result['files_edited']}")
        print("\n[QA]  Running tests after edit...")
        qa = run_qa(context=f"Last change: {result['files_edited']}")
        status = "✓ PASSED" if qa["passed"] else f"✗ FAILED after {qa['retries']} retries"
        print(f"  pytest: {status}")
        if not qa["passed"]:
            print(qa["final_output"][:600])
    else:
        print("\n  [No files edited — findings only]")

    _print_section("DONE")
    print(f"  specialist : {result['role']}")
    print(f"  mode       : {result['mode']}")
    print(f"  files edited: {len(result['files_edited'])}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("--review", "-r"):
        run_review()
    else:
        run_task(" ".join(args))

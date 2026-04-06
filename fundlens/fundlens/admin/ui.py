"""Gradio admin — professional fund reporting dashboard."""
from __future__ import annotations
import json
import re
import textwrap
import gradio as gr
from fundlens.server.data_store import store as global_store
from fundlens.models import Fund, Deal, Ownership, Cashflow
from fundlens.server.calculations import (
    compute_nav_bridge, compute_metrics,
    compute_portfolio_nav_bridge, compute_portfolio_metrics,
    compute_deal_nav_bridge, compute_deal_metrics,
)
from fundlens.server.seed_data import (
    load_easy_task, load_medium_task, load_hard_task,
)
from fundlens.admin.templates import (
    generate_onboarding_template, generate_cashflow_template, generate_quarterly_template,
    parse_onboarding_upload, parse_cashflow_upload, parse_quarterly_upload,
)
from fundlens.admin.export import export_answer_key

SECTORS    = ["Office", "Residential", "Logistics", "Data Center", "Industrial/Logistics",
              "Rental Studio & Apartment", "Retail"]
LOADERS    = {"easy": load_easy_task, "medium": load_medium_task, "hard": load_hard_task}

# Shared state: last AI test run results (for Answer Key tab)
_last_ai_run: dict = {"level": "", "fund_id": "", "deal_id": "",
                      "nav_cache": {}, "metrics_cache": {}, "reward": 0.0,
                      "correct_bridge": {}, "correct_metrics": {}}

# Internal CF type → human-readable label
_CF_LABEL = {
    "contribution": "Investment (Contribution)",
    "disposition":  "Disposition (ROC + G/L combined)",
    "income":       "Current Income",
}

# ── Helpers ────────────────────────────────────────────────────────────────

def _load_seed(task: str) -> str:
    LOADERS.get(task, load_easy_task)(global_store)
    return f"Loaded '{task}' — funds: {list(global_store.funds.keys())}"


def _portfolio_table():
    rows = []
    for fid, fund in global_store.funds.items():
        m = compute_metrics(fid, global_store)
        rows.append([
            fund.fund_name, fid,
            f"${fund.beginning_nav:.2f}M",
            f"${fund.ending_nav:.2f}M",
            f"{m.get('moic', 0):.3f}x",
            f"{m.get('irr', 0)*100:.1f}%",
        ])
    return rows


def _nav_bridge_table(fund_id: str):
    if fund_id not in global_store.funds:
        return []
    bridge = compute_nav_bridge(fund_id, global_store)
    labels = {
        "beginning_nav":         "Beginning NAV",
        "contribution":          "  (+) Contribution",
        "disposition":           "  (−) Disposition",
        "income":                "  (+) Income",
        "cashflow_adjusted_nav": "= Cashflow Adjusted NAV",
        "income_reversal":       "  (−) Income Reversal",
        "write_up_down":         "  (+/−) Write Up / Down (Plug)",
        "ending_nav":            "= Ending NAV",
    }
    return [[labels.get(k, k), f"${v:,.4f}M"] for k, v in bridge.items()]


def _deals_table(fund_id: str):
    rows = []
    for deal in global_store.get_deals_for_fund(fund_id):
        own      = global_store.get_ownership(fund_id, deal.deal_id)
        cfs      = global_store.get_cashflows(fund_id=fund_id, deal_id=deal.deal_id)
        invested = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
        distrib  = sum(c.fund_amt for c in cfs if c.cf_type in ("disposition", "income"))
        rows.append([
            deal.property_name, deal.sector, deal.location,
            f"{(own.ownership_pct * 100):.0f}%" if own else "100%",
            f"${invested:.2f}M", f"${distrib:.2f}M",
        ])
    return rows


def _cashflows_table(fund_id: str):
    rows = []
    for c in sorted(global_store.get_cashflows(fund_id=fund_id), key=lambda c: c.cash_date):
        deal = global_store.deals.get(c.deal_id)
        rows.append([
            c.cash_date,
            deal.property_name if deal else c.deal_id,
            _CF_LABEL.get(c.cf_type, c.cf_type),
            f"${c.fund_amt:,.4f}M",
        ])
    return rows


def _sector_table(fund_id: str):
    sector_data: dict = {}
    for deal in global_store.get_deals_for_fund(fund_id):
        sec = deal.sector or "Unknown"
        own = global_store.get_ownership(fund_id, deal.deal_id)
        own_pct = own.ownership_pct if own else 1.0
        cfs = global_store.get_cashflows(fund_id=fund_id, deal_id=deal.deal_id)
        inv = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
        dis = sum(c.fund_amt for c in cfs if c.cf_type in ("disposition", "income"))
        unrealized = deal.appraiser_nav * own_pct if deal.appraiser_nav else 0.0
        if sec not in sector_data:
            sector_data[sec] = {"invested": 0.0, "distributions": 0.0, "unrealized": 0.0, "count": 0}
        sector_data[sec]["invested"]    += inv
        sector_data[sec]["distributions"] += dis
        sector_data[sec]["unrealized"]  += unrealized
        sector_data[sec]["count"]       += 1
    rows = []
    for sec, d in sector_data.items():
        total_value = d["distributions"] + d["unrealized"]
        moic = (total_value / d["invested"]) if d["invested"] > 0 else 0
        rows.append([sec, d["count"],
                     f"${d['invested']:.2f}M", f"${d['distributions']:.2f}M",
                     f"${d['unrealized']:.2f}M", f"{moic:.3f}x"])
    return rows


def _deal_bridge_table(fund_id: str, deal_id: str):
    """8-line NAV bridge rows for one deal."""
    bridge = compute_deal_nav_bridge(fund_id, deal_id, global_store)
    if not bridge:
        return []
    return [[_BRIDGE_LABELS.get(k, k), f"${v:.4f}M"] for k, v in bridge.items()]


def _deal_metrics_table(fund_id: str, deal_id: str):
    """Deal-level metrics rows: MOIC, IRR, invested, distributions, current value."""
    dm = compute_deal_metrics(fund_id, deal_id, global_store)
    if not dm:
        return []
    rows = []
    labels = {
        "total_invested":    "Total Invested",
        "total_disposition": "Total Distributions (Dispositions)",
        "total_income":      "Total Income",
        "total_returned":    "Total Returned",
        "current_value":     "Current Value (Fund Share)",
        "moic":              "MOIC",
        "irr":               "IRR",
    }
    for k in ("total_invested", "total_disposition", "total_income",
              "total_returned", "current_value", "moic", "irr"):
        v = dm.get(k)
        if v is None:
            continue
        if k == "irr":
            rows.append([labels[k], f"{v * 100:.2f}%"])
        elif k == "moic":
            rows.append([labels[k], f"{v:.4f}x"])
        else:
            rows.append([labels[k], f"${v:.4f}M"])
    return rows


def _sector_irr_table(fund_id: str):
    """Sector breakdown with IRR per sector."""
    sector_data: dict = {}
    irr_map: dict = {}  # sector → {date: amount}

    for deal in global_store.get_deals_for_fund(fund_id):
        sec = deal.sector or "Unknown"
        own = global_store.get_ownership(fund_id, deal.deal_id)
        own_pct = own.ownership_pct if own else 1.0
        cfs = global_store.get_cashflows(fund_id=fund_id, deal_id=deal.deal_id)
        inv       = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
        dis       = sum(c.fund_amt for c in cfs if c.cf_type in ("disposition", "income"))
        unrealized = deal.appraiser_nav * own_pct if deal.appraiser_nav else 0.0

        if sec not in sector_data:
            sector_data[sec] = {"invested": 0.0, "distributions": 0.0, "unrealized": 0.0, "count": 0}
            irr_map[sec] = {}
        sector_data[sec]["invested"]      += inv
        sector_data[sec]["distributions"] += dis
        sector_data[sec]["unrealized"]    += unrealized
        sector_data[sec]["count"]         += 1

        # Accumulate cashflows for sector IRR
        from datetime import date as _date
        fund = global_store.funds.get(fund_id)
        for c in cfs:
            d = _date.fromisoformat(c.cash_date)
            irr_map[sec][d] = irr_map[sec].get(d, 0.0) + c.fund_amt
        if fund:
            td = _date.fromisoformat(fund.reporting_date)
            irr_map[sec][td] = irr_map[sec].get(td, 0.0) + unrealized

    from fundlens.server.calculations import calculate_xirr
    rows = []
    for sec, d in sector_data.items():
        total_value = d["distributions"] + d["unrealized"]
        moic = total_value / d["invested"] if d["invested"] > 0 else 0.0
        irr  = calculate_xirr(sorted(irr_map[sec].items())) if irr_map[sec] else 0.0
        rows.append([sec, d["count"],
                     f"${d['invested']:.2f}M", f"${d['distributions']:.2f}M",
                     f"${d['unrealized']:.2f}M", f"{moic:.3f}x", f"{irr*100:.2f}%"])
    return rows


# ── AI Test Run ───────────────────────────────────────────────────────────

_AI_SYSTEM_PROMPT = textwrap.dedent("""
    You are a PE fund analyst. Compute the NAV bridge and metrics yourself from raw data.

    TOOLS (call in this order):
      1. get_deal_info(fund_id)
         Returns per-deal: sector, ownership_pct, appraiser_nav, fund_share_nav,
         deal_beginning_nav (proportional, pre-computed), fund reporting_date, total_ending_nav.

      2. get_cashflow_summary(fund_id, deal_id?)   ← USE THIS, not get_raw_cashflows
         Returns pre-aggregated totals regardless of dataset size:
           total_contribution, total_disposition, total_income, irr_schedule
         Works for 10 rows or 100,000 rows — always compact.
         (get_raw_cashflows is paginated and only for audit/drill-down.)

      3. submit_report(nav_bridge, metrics)  — submit your computed answers

    NAV BRIDGE FORMULA (8 lines):
      beginning_nav         = deals[deal_id]["deal_beginning_nav"]  (fund level: fund_beginning_nav from get_deal_info)
      contribution          = total_contribution  (from get_cashflow_summary)  [positive]
      disposition           = total_disposition
      income                = total_income
      cashflow_adjusted_nav = beginning_nav + contribution - disposition + income
      income_reversal       = -income
      write_up_down         = ending_nav - (cashflow_adjusted_nav + income_reversal)  [THE PLUG]
      ending_nav            = total_ending_nav  (from get_deal_info)

    MOIC = (total_disposition + total_income + ending_nav) / total_contribution
    IRR  = XIRR on irr_schedule + append {date: reporting_date, net_amount: ending_nav}

    SUBMISSION FORMAT:
      easy:   submit_report(nav_bridge={8 keys}, metrics={})
      medium: submit_report(nav_bridge={8 keys}, metrics={"moic": value})
      hard:   submit_report(nav_bridge={8 keys}, metrics={"moic": value, "irr": value})

    The fund/deal to analyse is given in the user message.
    Respond ONLY with a JSON object:
    {"tool": "tool_name", "arguments": {"param": "value"}}
""").strip()

_BRIDGE_LABELS = {
    "beginning_nav":         "Beginning NAV",
    "contribution":          "(+) Contribution",
    "disposition":           "(−) Disposition",
    "income":                "(+) Income",
    "cashflow_adjusted_nav": "= Cashflow Adj. NAV",
    "income_reversal":       "(−) Income Reversal",
    "write_up_down":         "(+/−) Write Up / Down (Plug)",
    "ending_nav":            "= Ending NAV",
}


def _run_ai_test(api_key: str, base_url: str, model_name: str, task_id: str,
                 level: str = "Fund", fund_id: str = "", deal_id: str = ""):
    """Run the AI agent against a task (or specific fund/deal). Returns (log, comparison, reward)."""
    try:
        from openai import OpenAI
        from openenv.core.env_server import CallToolAction
        from fundlens.server.environment import FundLensEnvironment
    except ImportError as e:
        return f"Import error: {e}", [], "—"

    if not api_key or not api_key.strip():
        return "No API key provided.", [], "—"

    logs = []
    comparison = []
    reward = 0.0
    nav_cache: dict = {}
    metrics_cache: dict = {}
    tool_call_counts: dict = {}   # loop detection

    try:
        client = OpenAI(base_url=base_url.strip(), api_key=api_key.strip())
        env = FundLensEnvironment()
        # Always load "hard" so ALL funds are available regardless of which fund user picks
        obs = env.reset(task_id="hard")

        target_fund = fund_id.strip() if fund_id and fund_id.strip() else (
            obs.available_funds[0] if obs.available_funds else "alpha"
        )
        target_deal = deal_id.strip() if deal_id and deal_id.strip() else ""
        effective_level = level if level else "Fund"

        # Pre-compute correct answers from the AI's own store (avoids global_store mismatch)
        env_store = env._store
        if effective_level == "Portfolio":
            pre_correct_bridge  = compute_portfolio_nav_bridge(env_store)
            pre_correct_metrics = compute_portfolio_metrics(env_store)
        elif effective_level == "Investment/Deal" and target_deal:
            pre_correct_bridge  = compute_deal_nav_bridge(target_fund, target_deal, env_store)
            pre_correct_metrics = compute_deal_metrics(target_fund, target_deal, env_store)
        else:
            pre_correct_bridge  = compute_nav_bridge(target_fund, env_store)
            pre_correct_metrics = compute_metrics(target_fund, env_store)

        # Build task description based on level
        mode_suffix = {
            "easy":   "submit_report(nav_bridge=..., metrics={}).",
            "medium": "submit_report(nav_bridge=..., metrics={\"moic\": value}).",
            "hard":   "submit_report(nav_bridge=..., metrics={\"moic\": value, \"irr\": value}).",
        }.get(task_id, "")

        if effective_level == "Portfolio":
            task_desc = (
                f"Compute the combined NAV bridge and metrics for ALL funds: {obs.available_funds}.\n"
                f"1. Call get_deal_info(fund_id) for EACH fund to get beginning_nav, ending_nav per deal.\n"
                f"2. Call get_raw_cashflows(fund_id) for EACH fund to get all transactions.\n"
                f"3. Sum cashflows across ALL funds. Compute the 8-line NAV bridge using the formula.\n"
                f"4. Compute MOIC from all cashflows combined.\n"
                f"5. {mode_suffix}"
            )
            logs.append(f"Level : Portfolio  |  Funds: {obs.available_funds}")
        elif effective_level == "Investment/Deal" and target_deal:
            task_desc = (
                f"Compute the NAV bridge and metrics for deal '{target_deal}' in fund '{target_fund}'.\n"
                f"1. Call get_deal_info('{target_fund}') → find deal '{target_deal}' in the 'deals' dict.\n"
                f"   Use deals['{target_deal}']['deal_beginning_nav'] as beginning_nav (NOT fund_beginning_nav).\n"
                f"   Use deals['{target_deal}']['fund_share_nav'] as ending_nav.\n"
                f"2. Call get_raw_cashflows(fund_id='{target_fund}', deal_id='{target_deal}') "
                f"to get this deal's cashflows only.\n"
                f"3. Compute the 8-line NAV bridge using: contribution=sum(abs) of contributions, "
                f"disposition=sum of dispositions, income=sum of income cashflows.\n"
                f"4. Compute MOIC and IRR from this deal's cashflows only.\n"
                f"5. {mode_suffix}"
            )
            logs.append(f"Level : Investment  |  Fund: {target_fund}  |  Deal: {target_deal}")
        else:
            task_desc = (
                f"Compute the NAV bridge and metrics for fund '{target_fund}'.\n"
                f"1. Call get_deal_info('{target_fund}') to get beginning_nav, deals, and ending_nav.\n"
                f"2. Call get_raw_cashflows(fund_id='{target_fund}') to get all fund cashflows.\n"
                f"3. Compute the 8-line NAV bridge using the formula.\n"
                f"   ending_nav = sum of (appraiser_nav * ownership_pct) across all deals.\n"
                f"4. Compute MOIC and IRR from all cashflows + ending_nav as terminal value.\n"
                f"5. {mode_suffix}"
            )
            logs.append(f"Level : Fund  |  Fund: {target_fund}")

        logs.append(f"Mode  : {task_id}")
        logs.append("─" * 60)

        messages = [
            {"role": "system", "content": _AI_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"{task_desc}\n\n"
                f"Available fund IDs: {obs.available_funds}\n"
                "Start now."
            )},
        ]

        for step in range(1, 12):
            if env.state.is_done:
                break

            resp = client.chat.completions.create(
                model=model_name.strip(), messages=messages,
                temperature=0.7, max_tokens=800,
            )
            content = resp.choices[0].message.content or ""

            # Parse JSON tool call from response
            s = content.find("{")
            e = content.rfind("}") + 1
            tool_call = None
            if s != -1 and e > 0:
                try:
                    tool_call = json.loads(content[s:e])
                except json.JSONDecodeError:
                    pass

            if not tool_call:
                logs.append(f"Step {step:2d}: [could not parse JSON — retrying]")
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user",
                                  "content": 'Respond with JSON only: {"tool": "...", "arguments": {...}}'})
                continue

            tool_name = tool_call.get("tool", "")
            arguments = tool_call.get("arguments", {})

            # Loop detection — if same tool called 3+ times, force submission
            tool_call_counts[tool_name] = tool_call_counts.get(tool_name, 0) + 1
            if tool_call_counts[tool_name] >= 3 and tool_name != "submit_report":
                logs.append(f"Step {step:2d}: [LOOP DETECTED — {tool_name} called {tool_call_counts[tool_name]}x — forcing submit]")
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": (
                    f"You have called {tool_name} {tool_call_counts[tool_name]} times already. "
                    "You have all the data you need. Call submit_report NOW with whatever values you have."
                )})
                continue

            logs.append(f"Step {step:2d}: {tool_name}({json.dumps(arguments)[:100]})")

            step_obs = env.step(CallToolAction(tool_name=tool_name, arguments=arguments))
            result = step_obs.result.data if step_obs.result else None
            result_str = json.dumps(result)[:4000] if result else str(step_obs.error)
            logs.append(f"        → {result_str[:300]}")

            # Capture what the AI computed and submitted
            if tool_name == "submit_report" and isinstance(arguments, dict):
                submitted_bridge  = arguments.get("nav_bridge", {})
                submitted_metrics = arguments.get("metrics", {})
                if isinstance(submitted_bridge, dict):
                    nav_cache = submitted_bridge
                if isinstance(submitted_metrics, dict):
                    metrics_cache.update(submitted_metrics)

            if isinstance(result, dict) and "reward" in result:
                reward = result["reward"]
                logs.append("─" * 60)
                logs.append("Submission received.")
                break

            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": (
                f"Result: {result_str[:3500]}\n\n"
                "Continue — call the next tool, or submit_report() if you have all values."
            )})
        else:
            logs.append("Max steps reached without a submission.")

        # Build comparison directly — no global state, no stale data risk
        comparison = _build_comparison(
            pre_correct_bridge, pre_correct_metrics,
            nav_cache, metrics_cache,
        )
        # Also update shared state so Answer Key tab "Compare vs Last AI Run" works
        _last_ai_run.update({
            "level":           effective_level,
            "fund_id":         target_fund,
            "deal_id":         target_deal,
            "nav_cache":       nav_cache,
            "metrics_cache":   metrics_cache,
            "reward":          reward,
            "correct_bridge":  pre_correct_bridge,
            "correct_metrics": pre_correct_metrics,
        })

    except Exception as exc:
        logs.append(f"\nERROR: {exc}")

    # Score from comparison rows (not submit_report which always grades against alpha)
    pass_count  = sum(1 for r in comparison if r and "✔" in str(r[3]))
    total_count = len([r for r in comparison if r and str(r[3]) not in ("", None)])
    local_score = pass_count / total_count if total_count > 0 else 0.0
    reward_text = f"{local_score:.4f} / 1.0000  ({pass_count}/{total_count} items correct)"
    return "\n".join(logs), comparison, reward_text


# ── Answer Key helpers ────────────────────────────────────────────────────

_DEAL_METRIC_LABELS = {
    "total_invested":    "Total Invested",
    "total_disposition": "Total Disposition",
    "total_income":      "Total Income",
    "total_returned":    "Total Returned",
    "current_value":     "Current Value (Fund Share)",
    "moic":              "MOIC",
    "irr":               "IRR",
}


def _fmt_val(key: str, val) -> str:
    if val is None or val == "":
        return "—"
    if key == "irr":
        return f"{val * 100:.2f}%"
    if key in ("moic",):
        return f"{val:.4f}x"
    if key == "ownership_pct":
        return f"{val * 100:.1f}%"
    return f"${val:.4f}M"


def _get_seed_store(level: str, fund_id: str):
    """Return a DataStore preloaded with hard task seed data (all 3 funds).
    Used by Answer Key tab which doesn't depend on global_store state."""
    from fundlens.server.data_store import DataStore
    s = DataStore()
    load_hard_task(s)
    return s


def _correct_answer_rows(level: str, fund_id: str, deal_id: str):
    """Return (bridge_rows, metrics_rows) for the selected level.
    Always uses a fresh seed DataStore so results are independent of admin DB state."""
    bridge_rows, metrics_rows = [], []
    s = _get_seed_store(level, fund_id)

    if level == "Portfolio":
        bridge  = compute_portfolio_nav_bridge(s)
        metrics = compute_portfolio_metrics(s)
        for k, v in bridge.items():
            bridge_rows.append([_BRIDGE_LABELS.get(k, k), _fmt_val(k, v)])
        if metrics:
            metrics_rows.append(["MOIC", _fmt_val("moic", metrics.get("moic"))])
            metrics_rows.append(["IRR",  _fmt_val("irr",  metrics.get("irr"))])

    elif level == "Fund" and fund_id:
        bridge  = compute_nav_bridge(fund_id, s)
        metrics = compute_metrics(fund_id, s)
        for k, v in bridge.items():
            bridge_rows.append([_BRIDGE_LABELS.get(k, k), _fmt_val(k, v)])
        if metrics:
            metrics_rows.append(["MOIC", _fmt_val("moic", metrics.get("moic"))])
            metrics_rows.append(["IRR",  _fmt_val("irr",  metrics.get("irr"))])

    elif level == "Investment/Deal" and fund_id and deal_id:
        bridge = compute_deal_nav_bridge(fund_id, deal_id, s)
        dm     = compute_deal_metrics(fund_id, deal_id, s)
        for k, v in bridge.items():
            bridge_rows.append([_BRIDGE_LABELS.get(k, k), _fmt_val(k, v)])
        for k in ("total_invested", "total_disposition", "total_income",
                  "total_returned", "current_value", "moic", "irr"):
            metrics_rows.append([_DEAL_METRIC_LABELS.get(k, k), _fmt_val(k, dm.get(k))])

    return bridge_rows, metrics_rows


def _build_comparison(correct_bridge: dict, correct_metrics: dict,
                       nav_cache: dict, metrics_cache: dict) -> list:
    """Build comparison rows from precomputed correct values and AI cache.
    Returns [Line Item, AI's Answer, Correct Answer, Pass/Fail].
    Pure function — no global state."""
    rows = []

    # Bridge lines
    for k, cv in correct_bridge.items():
        av    = nav_cache.get(k)
        label = _BRIDGE_LABELS.get(k, k)
        cv_s  = _fmt_val(k, cv)
        if av is not None:
            diff = abs(float(av) - float(cv))
            ok   = diff <= 0.5
            rows.append([label, _fmt_val(k, av), cv_s,
                         "✔ Pass" if ok else f"✗ Fail  (off by ${diff:.4f}M)"])
        else:
            rows.append([label, "— not submitted", cv_s, "✗ Missing"])

    # Metric lines
    skip_keys = {"ownership_pct", "total_returned"}
    for k, cv in correct_metrics.items():
        if k in skip_keys:
            continue
        av    = metrics_cache.get(k)
        label = _DEAL_METRIC_LABELS.get(k, k.upper())
        tol   = 0.01 if k == "irr" else (0.02 if k == "moic" else 0.5)
        cv_s  = _fmt_val(k, cv)
        if av is not None:
            diff = abs(float(av) - float(cv))
            ok   = diff <= tol
            rows.append([label, _fmt_val(k, av), cv_s,
                         "✔ Pass" if ok else f"✗ Fail  (off by {diff:.4f})"])
        else:
            rows.append([label, "— not submitted", cv_s, "✗ Missing"])

    return rows


def _comparison_rows(level: str, fund_id: str, deal_id: str):
    """Return comparison rows: [Line Item, AI's Answer, Correct Answer, Pass/Fail].
    Columns match the table header order in the AI Test Run tab.
    Correct values come from _last_ai_run (computed from the AI's own store)."""
    rows = []
    last = _last_ai_run

    bridge  = last.get("correct_bridge", {})
    metrics = last.get("correct_metrics", {})

    if not bridge and not metrics:
        return []

    # Bridge lines
    for k, cv in bridge.items():
        av    = last["nav_cache"].get(k)
        label = _BRIDGE_LABELS.get(k, k)
        cv_s  = _fmt_val(k, cv)
        if av is not None:
            diff = abs(av - cv)
            ok   = diff <= 0.5
            rows.append([label, _fmt_val(k, av), cv_s,
                         "✔ Pass" if ok else f"✗ Fail  (off by ${diff:.4f}M)"])
        else:
            rows.append([label, "— not submitted", cv_s, "✗ Missing"])

    # Metric lines
    skip_keys = {"ownership_pct", "total_returned"}
    for k, cv in metrics.items():
        if k in skip_keys:
            continue
        av    = last["metrics_cache"].get(k)
        label = _DEAL_METRIC_LABELS.get(k, k.upper())
        tol   = 0.01 if k == "irr" else (0.02 if k == "moic" else 0.5)
        cv_s  = _fmt_val(k, cv)
        if av is not None:
            diff = abs(av - cv)
            ok   = diff <= tol
            rows.append([label, _fmt_val(k, av), cv_s,
                         "✔ Pass" if ok else f"✗ Fail  (off by {diff:.4f})"])
        else:
            rows.append([label, "— not submitted", cv_s, "✗ Missing"])

    return rows


# ── Build UI ───────────────────────────────────────────────────────────────

def build_admin_ui() -> gr.Blocks:
    with gr.Blocks(title="FundLens — PE Fund Reporting") as demo:

        gr.HTML("""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                    padding: 24px 32px; border-radius: 12px; margin-bottom: 8px;">
            <h1 style="color: #e2e8f0; margin: 0; font-size: 26px; font-weight: 700;
                       letter-spacing: -0.5px;">
                🏢 FundLens
            </h1>
            <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 14px;">
                PE Fund NAV Bridge &amp; Reporting Platform &nbsp;·&nbsp; Real Estate Private Equity
            </p>
        </div>
        """)

        # ── Quick Load Bar ─────────────────────────────────────────────────
        with gr.Row():
            seed_choice = gr.Dropdown(
                choices=["easy", "medium", "hard"], value="easy",
                label="Load Task Dataset", scale=1,
            )
            load_btn    = gr.Button("Load Dataset", variant="primary", scale=1)
            load_status = gr.Textbox(label="Status", interactive=False, scale=4)

        load_btn.click(_load_seed, inputs=[seed_choice], outputs=[load_status])

        with gr.Tabs():

            # ════════════════════════════════════════════════════════════════
            # Tab 1 — Portfolio Dashboard
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("📊 Portfolio Dashboard"):
                gr.Markdown("### Portfolio Summary — All Funds")
                refresh_portfolio = gr.Button("Refresh", variant="secondary")
                portfolio_table = gr.Dataframe(
                    headers=["Fund Name", "ID", "Beginning NAV", "Ending NAV", "MOIC", "IRR"],
                    datatype=["str"]*6, column_count=6, wrap=True,
                    label="Fund Performance",
                )
                refresh_portfolio.click(_portfolio_table, outputs=[portfolio_table])
                load_btn.click(_portfolio_table, outputs=[portfolio_table])

            # ════════════════════════════════════════════════════════════════
            # Tab 2 — NAV Bridge
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("📋 NAV Bridge"):
                gr.Markdown(
                    "### NAV Bridge (8-Line Valuation Walk)\n"
                    "Write Up/Down is always the **derived plug** — never entered manually."
                )
                with gr.Row():
                    bridge_level = gr.Radio(
                        choices=["Portfolio", "Fund", "Investment/Deal"],
                        value="Fund", label="Analysis Level", scale=3,
                    )
                    bridge_fund = gr.Dropdown(choices=[], label="Fund", scale=2, visible=True)
                    bridge_deal = gr.Dropdown(choices=[], label="Deal", scale=2, visible=False)
                    bridge_btn  = gr.Button("Compute NAV Bridge", variant="primary", scale=1)

                bridge_table = gr.Dataframe(
                    headers=["Line Item", "Amount (USD M)"],
                    datatype=["str", "str"], column_count=2, label="NAV Bridge",
                )
                metrics_table = gr.Dataframe(
                    headers=["Metric", "Value"],
                    datatype=["str", "str"], column_count=2, label="Performance Metrics",
                )

                def _bridge_level_toggle(lvl):
                    return (
                        gr.update(visible=lvl in ("Fund", "Investment/Deal")),
                        gr.update(visible=lvl == "Investment/Deal"),
                    )

                def _bridge_update_deals(fid):
                    if not fid:
                        return gr.update(choices=[], value=None)
                    deals = [d.deal_id for d in global_store.get_deals_for_fund(fid)]
                    return gr.update(choices=deals, value=deals[0] if deals else None)

                bridge_level.change(_bridge_level_toggle, inputs=[bridge_level],
                                    outputs=[bridge_fund, bridge_deal])
                bridge_fund.change(_bridge_update_deals, inputs=[bridge_fund],
                                   outputs=[bridge_deal])

                def compute_bridge_and_metrics(lvl, fid, did):
                    if lvl == "Portfolio":
                        bridge = compute_portfolio_nav_bridge(global_store)
                        m      = compute_portfolio_metrics(global_store)
                        bridge_rows  = [[_BRIDGE_LABELS.get(k, k), f"${v:.4f}M"]
                                        for k, v in bridge.items()]
                        metrics_rows = [
                            ["MOIC", f"{m.get('moic', 0):.4f}x"],
                            ["IRR",  f"{m.get('irr', 0)*100:.2f}%"],
                        ] if m else []
                    elif lvl == "Investment/Deal" and fid and did:
                        bridge = compute_deal_nav_bridge(fid, did, global_store)
                        dm     = compute_deal_metrics(fid, did, global_store)
                        bridge_rows  = [[_BRIDGE_LABELS.get(k, k), f"${v:.4f}M"]
                                        for k, v in bridge.items()]
                        metrics_rows = []
                        if dm:
                            metrics_rows = [
                                ["Total Invested",   f"${dm.get('total_invested', 0):.4f}M"],
                                ["Total Returned",   f"${dm.get('total_returned', 0):.4f}M"],
                                ["Current Value",    f"${dm.get('current_value', 0):.4f}M"],
                                ["MOIC",             f"{dm.get('moic', 0):.4f}x"],
                                ["IRR",              f"{dm.get('irr', 0)*100:.2f}%"],
                                ["Ownership %",      f"{dm.get('ownership_pct', 1)*100:.1f}%"],
                            ]
                    else:  # Fund
                        bridge_rows = _nav_bridge_table(fid)
                        if fid not in global_store.funds:
                            return bridge_rows, []
                        m = compute_metrics(fid, global_store)
                        metrics_rows = [
                            ["MOIC", f"{m.get('moic', 0):.4f}x"],
                            ["IRR",  f"{m.get('irr', 0)*100:.2f}%"],
                        ]
                    return bridge_rows, metrics_rows

                bridge_btn.click(
                    compute_bridge_and_metrics,
                    inputs=[bridge_level, bridge_fund, bridge_deal],
                    outputs=[bridge_table, metrics_table],
                )

            # ════════════════════════════════════════════════════════════════
            # Tab 3 — Deal Explorer
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("🏗️ Deal Explorer"):
                gr.Markdown("### Deals by Fund")
                with gr.Row():
                    deals_fund = gr.Dropdown(choices=[], label="Select Fund", scale=2)
                    deals_btn  = gr.Button("Load Deals", variant="primary", scale=1)

                deals_table = gr.Dataframe(
                    headers=["Property", "Sector", "Location",
                             "Ownership %", "Invested (USD M)", "Distributions (USD M)"],
                    datatype=["str"]*6, column_count=6, label="Deal Summary",
                )
                sector_table_view = gr.Dataframe(
                    headers=["Sector", "# Deals", "Total Invested", "Total Distributions",
                             "Unrealized NAV", "MOIC", "IRR"],
                    datatype=["str"]*7, column_count=7, label="Sector Breakdown (with IRR)",
                )

                gr.HTML("<hr style='border-color:#1e293b;margin:18px 0 14px'>")
                gr.Markdown("### Investment / Deal Deep-Dive")
                with gr.Row():
                    deal_detail_dd = gr.Dropdown(choices=[], label="Select Deal", scale=2)
                    deal_detail_btn = gr.Button("Compute Deal Analytics", variant="primary", scale=1)

                with gr.Row():
                    deal_bridge_tbl = gr.Dataframe(
                        headers=["NAV Bridge Line", "Value (USD M)"],
                        datatype=["str"]*2, column_count=2,
                        label="Deal NAV Bridge (8-line)",
                    )
                    deal_metrics_tbl = gr.Dataframe(
                        headers=["Metric", "Value"],
                        datatype=["str"]*2, column_count=2,
                        label="Deal Performance Metrics",
                    )

                def _load_deals_and_dropdowns(fid):
                    dt = _deals_table(fid)
                    st = _sector_irr_table(fid)
                    deal_ids = [d.deal_id for d in global_store.get_deals_for_fund(fid)]
                    dd_upd = gr.update(choices=deal_ids, value=deal_ids[0] if deal_ids else None)
                    return dt, st, dd_upd

                deals_btn.click(
                    _load_deals_and_dropdowns,
                    inputs=[deals_fund],
                    outputs=[deals_table, sector_table_view, deal_detail_dd],
                )

                deal_detail_btn.click(
                    lambda fid, did: (_deal_bridge_table(fid, did), _deal_metrics_table(fid, did)),
                    inputs=[deals_fund, deal_detail_dd],
                    outputs=[deal_bridge_tbl, deal_metrics_tbl],
                )

            # ════════════════════════════════════════════════════════════════
            # Tab 4 — Cashflow Ledger
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("📒 Cashflow Ledger"):
                gr.Markdown("### All Cashflows for a Fund")
                with gr.Row():
                    cf_fund_view = gr.Dropdown(choices=[], label="Select Fund", scale=2)
                    cf_view_btn  = gr.Button("Load Cashflows", variant="primary", scale=1)

                cf_table_view = gr.Dataframe(
                    headers=["Date", "Deal", "Type", "Fund Amount (USD M)"],
                    datatype=["str"]*4, column_count=4, label="Cashflow Ledger",
                )
                cf_view_btn.click(_cashflows_table, inputs=[cf_fund_view], outputs=[cf_table_view])

            # ════════════════════════════════════════════════════════════════
            # Tab 5 — Onboarding
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("🏛️ Onboarding"):

                # ── Bulk Upload Banner ────────────────────────────────────
                gr.HTML("""
                <div style="background:#1e3a5f;border-left:4px solid #3b82f6;
                            padding:12px 16px;border-radius:6px;margin-bottom:16px;">
                  <p style="color:#e2e8f0;margin:0 0 6px 0;font-weight:600;font-size:13px;">
                    📤 Bulk Upload (recommended for large portfolios)
                  </p>
                  <p style="color:#94a3b8;margin:0;font-size:12px;line-height:1.6;">
                    Download the Excel template → fill both sheets (Funds + Investments)
                    → upload the completed file.<br>
                    Manual entry below works just as well for small additions.
                  </p>
                </div>
                """)
                with gr.Row():
                    ob_dl_btn  = gr.Button("⬇  Download Onboarding Template",
                                           variant="secondary", scale=2)
                    ob_ul_file = gr.File(label="Upload Completed Template (.xlsx)",
                                         file_types=[".xlsx"], scale=3)
                    ob_ul_btn  = gr.Button("Process Upload", variant="primary", scale=1)
                ob_dl_file  = gr.File(label="Template ready", visible=False)
                ob_ul_status = gr.Textbox(label="Upload Result", interactive=False,
                                          show_label=False)

                gr.HTML("<hr style='border-color:#1e293b;margin:18px 0 14px'>")

                # ── 1. Fund Onboarding Table ──────────────────────────────
                gr.HTML("""
                <p style="font-size:15px;font-weight:700;color:#e2e8f0;margin:4px 0 14px;">
                  1 &nbsp;&nbsp; Fund Onboarding Table
                </p>""")

                with gr.Row():
                    ob_fname = gr.Textbox(label="Fund Name",
                                          placeholder="RE Alpha Fund I", scale=3)
                    ob_fqtr  = gr.Textbox(label="Onboarded Quarter / Date",
                                          placeholder="Q1 2022  or  2022-03-31", scale=2)
                    ob_fadd  = gr.Button("Add Fund", variant="primary", scale=1)
                ob_fstatus = gr.Textbox(label="", interactive=False, show_label=False)
                ob_ftbl = gr.Dataframe(
                    headers=["Fund Name", "Onboarded Quarter / Date"],
                    datatype=["str"]*2, column_count=2, label="", wrap=True,
                )

                gr.HTML("<hr style='border-color:#1e293b;margin:22px 0'>")

                # ── 2. Investment Onboarding Table ────────────────────────
                gr.HTML("""
                <p style="font-size:15px;font-weight:700;color:#e2e8f0;margin:4px 0 4px;">
                  2 &nbsp;&nbsp; Investment Onboarding Table
                </p>
                <p style="color:#94a3b8;font-size:12px;margin:0 0 14px;">
                  One row per deal–fund relationship.
                  Co-investments = one row per fund at their respective ownership %.
                </p>""")

                with gr.Row():
                    ob_dname = gr.Textbox(label="Deal Name",
                                          placeholder="BKC Commercial Tower", scale=3)
                    ob_ifund = gr.Dropdown(choices=[], label="Fund Name (investing fund)",
                                           scale=2)
                    ob_sector = gr.Dropdown(
                        choices=SECTORS, label="Sector", scale=2,
                        value="Office", allow_custom_value=True,
                    )
                    ob_location = gr.Textbox(label="Location",
                                             placeholder="Mumbai, India", scale=2)
                with gr.Row():
                    ob_opct  = gr.Number(label="Fund's Agreed Ownership %",
                                         value=100.0, scale=1)
                    ob_iqtr  = gr.Textbox(label="Onboarded Quarter / Date",
                                          placeholder="Q1 2022", scale=2)
                    ob_iadd  = gr.Button("Add Investment", variant="primary", scale=2)
                ob_istatus = gr.Textbox(label="", interactive=False, show_label=False)
                ob_itbl = gr.Dataframe(
                    headers=["Deal Name", "Sector", "Location",
                             "Fund Name (investing fund)",
                             "Fund's Agreed Ownership", "Onboarded Quarter / Date"],
                    datatype=["str"]*6, column_count=6, label="", wrap=True,
                )

                # ── Handlers ──────────────────────────────────────────────

                def _ob_fund_rows():
                    return [
                        [f.fund_name, f.nav_period_start or "—"]
                        for f in global_store.funds.values()
                    ]

                def _ob_inv_rows():
                    rows = []
                    for o in global_store.ownerships:
                        deal = global_store.deals.get(o.deal_id)
                        fund = global_store.funds.get(o.fund_id)
                        rows.append([
                            deal.property_name if deal else o.deal_id,
                            deal.sector if deal else "—",
                            deal.location if deal else "—",
                            fund.fund_name if fund else o.fund_id,
                            f"{o.ownership_pct * 100:.0f}%",
                            o.entry_date or "—",
                        ])
                    return rows

                def _fund_name_choices():
                    return [f.fund_name for f in global_store.funds.values()]

                def add_fund_entry(fname, fqtr):
                    if not fname:
                        return "Error: Fund Name is required", _ob_fund_rows(), gr.update()
                    fid = re.sub(r'[^a-z0-9]+', '_', fname.lower()).strip('_')
                    global_store.add_fund(Fund(
                        fund_id=fid, fund_name=fname,
                        reporting_date="", nav_period_start=fqtr or "",
                        beginning_nav=0.0, ending_nav=0.0,
                    ))
                    names = _fund_name_choices()
                    return (
                        f"Added: '{fname}' — {len(global_store.funds)} fund(s). "
                        "Enter NAV in the Quarterly Inputs tab.",
                        _ob_fund_rows(),
                        gr.update(choices=names, value=fname),
                    )

                def add_inv_entry(dname, fname, sector, location, opct, iqtr):
                    if not dname or not fname:
                        return "Error: Deal Name and Fund Name are required", _ob_inv_rows()
                    fund = next((f for f in global_store.funds.values()
                                 if f.fund_name == fname), None)
                    if not fund:
                        return (f"Error: '{fname}' not in registry — "
                                "add the fund first"), _ob_inv_rows()
                    did = re.sub(r'[^a-z0-9]+', '_', dname.lower()).strip('_')
                    if did not in global_store.deals:
                        global_store.add_deal(Deal(
                            deal_id=did, property_name=dname,
                            sector=sector or "Other",
                            location=location or "",
                        ))
                    else:
                        # update sector/location if deal already exists without them
                        existing = global_store.deals[did]
                        if not existing.sector and sector:
                            existing.sector = sector
                        if not existing.location and location:
                            existing.location = location
                    global_store.add_ownership(Ownership(
                        fund_id=fund.fund_id, deal_id=did,
                        ownership_pct=(opct or 100.0) / 100.0,
                        entry_date=iqtr or "",
                    ))
                    return (
                        f"Added: '{dname}' [{sector or 'Other'}] → {fname} at {opct:.0f}% — "
                        f"{len(global_store.ownerships)} investment row(s). "
                        "Enter cashflows in the Cashflow Entry tab.",
                        _ob_inv_rows(),
                    )

                def process_ob_upload(file_obj):
                    if file_obj is None:
                        return ("No file selected", _ob_fund_rows(),
                                _ob_inv_rows(), gr.update())
                    filepath = (getattr(file_obj, 'path', None)
                                or getattr(file_obj, 'name', None)
                                or str(file_obj))
                    funds_data, invs_data, err = parse_onboarding_upload(filepath)
                    if err:
                        return (f"Error: {err}", _ob_fund_rows(),
                                _ob_inv_rows(), gr.update())
                    added_f = 0
                    for fd in funds_data:
                        fid = re.sub(r'[^a-z0-9]+', '_', fd['name'].lower()).strip('_')
                        global_store.add_fund(Fund(
                            fund_id=fid, fund_name=fd['name'],
                            reporting_date='', nav_period_start=fd.get('quarter', ''),
                            beginning_nav=0.0, ending_nav=0.0,
                        ))
                        added_f += 1
                    added_i = 0
                    for inv in invs_data:
                        fund = next((f for f in global_store.funds.values()
                                     if f.fund_name == inv['fund_name']), None)
                        if not fund:
                            continue
                        did = re.sub(r'[^a-z0-9]+', '_',
                                     inv['deal_name'].lower()).strip('_')
                        if did not in global_store.deals:
                            global_store.add_deal(Deal(
                                deal_id=did, property_name=inv['deal_name'],
                                sector='', location='',
                            ))
                        global_store.add_ownership(Ownership(
                            fund_id=fund.fund_id, deal_id=did,
                            ownership_pct=inv.get('ownership_pct', 100.0) / 100.0,
                            entry_date=inv.get('quarter', ''),
                        ))
                        added_i += 1
                    names = _fund_name_choices()
                    return (
                        f"Imported {added_f} fund(s) and {added_i} investment(s).",
                        _ob_fund_rows(),
                        _ob_inv_rows(),
                        gr.update(choices=names, value=names[0] if names else None),
                    )

                ob_fadd.click(add_fund_entry,
                    inputs=[ob_fname, ob_fqtr],
                    outputs=[ob_fstatus, ob_ftbl, ob_ifund])
                ob_iadd.click(add_inv_entry,
                    inputs=[ob_dname, ob_ifund, ob_sector, ob_location, ob_opct, ob_iqtr],
                    outputs=[ob_istatus, ob_itbl])
                ob_dl_btn.click(generate_onboarding_template, outputs=[ob_dl_file])
                ob_dl_btn.click(
                    lambda: gr.update(visible=True), outputs=[ob_dl_file]
                )
                ob_ul_btn.click(
                    process_ob_upload,
                    inputs=[ob_ul_file],
                    outputs=[ob_ul_status, ob_ftbl, ob_itbl, ob_ifund],
                )

            # ════════════════════════════════════════════════════════════════
            # Tab 6 — Cashflow Entry
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("💰 Cashflow Entry"):
                gr.HTML("""
                <div style="background:#1e293b;border-left:4px solid #f59e0b;
                            padding:12px 16px;border-radius:6px;margin-bottom:14px;
                            font-size:12px;color:#94a3b8;line-height:1.7;">
                  <b style="color:#e2e8f0;font-size:13px;">Transaction Types (all amounts in USD M)</b><br>
                  <b style="color:#fbbf24;">Investment (Contribution)</b> — capital call / drawdown
                  (enter as <b style="color:#e2e8f0;">negative</b> amount).<br>
                  <b style="color:#fbbf24;">Current Income</b> — rent / yield distribution
                  (positive amount).<br>
                  <b style="color:#fbbf24;">Disposition</b> — property sale proceeds
                  (positive amount, inclusive of ROC + G/L + FX — combined at fund level).
                </div>
                """)

                # ── Bulk Upload ───────────────────────────────────────────
                gr.HTML("""
                <div style="background:#1e3a5f;border-left:4px solid #3b82f6;
                            padding:10px 14px;border-radius:6px;margin-bottom:14px;">
                  <p style="color:#e2e8f0;margin:0 0 4px 0;font-weight:600;font-size:13px;">
                    📤 Bulk Upload Cashflows
                  </p>
                  <p style="color:#94a3b8;margin:0;font-size:12px;">
                    Download template → fill rows (one row per cashflow) → upload.
                  </p>
                </div>
                """)
                with gr.Row():
                    ce_dl_btn  = gr.Button("⬇  Download Cashflow Template",
                                           variant="secondary", scale=2)
                    ce_ul_file = gr.File(label="Upload Completed Template (.xlsx)",
                                         file_types=[".xlsx"], scale=3)
                    ce_ul_btn  = gr.Button("Process Upload", variant="primary", scale=1)
                ce_dl_file  = gr.File(label="Template ready", visible=False)
                ce_ul_status = gr.Textbox(label="Upload Result", interactive=False,
                                          show_label=False)

                gr.HTML("<hr style='border-color:#1e293b;margin:14px 0'>")

                # ── Fund / Deal selection ─────────────────────────────────
                with gr.Row():
                    ce_fund_dd  = gr.Dropdown(choices=[], label="Fund", scale=2)
                    ce_deal_dd  = gr.Dropdown(choices=[], label="Investment (Deal)", scale=3)
                    ce_view_btn = gr.Button("Refresh Ledger", variant="secondary", scale=1)

                # ── Cashflow Entry Row ────────────────────────────────────
                with gr.Row():
                    ce_date = gr.Textbox(label="Date (YYYY-MM-DD)",
                                         placeholder="2024-03-15", scale=2)
                    ce_type = gr.Dropdown(
                        ["Investment", "Current Income", "Disposition"],
                        label="Transaction Type", scale=2,
                    )
                    ce_amt = gr.Number(
                        label="Fund Amount (USD M — negative for contributions)",
                        value=None, scale=3,
                    )
                    ce_add_btn = gr.Button("Add Cashflow", variant="primary", scale=1)

                ce_status = gr.Textbox(label="Result", interactive=False)

                ce_ledger = gr.Dataframe(
                    headers=["Date", "Fund", "Deal", "Type", "Fund Amount (USD M)"],
                    datatype=["str"]*5, column_count=5,
                    label="Cashflow Ledger",
                )

                # ── Handlers ──────────────────────────────────────────────

                def _update_ce_deals(fid):
                    deals = global_store.get_deals_for_fund(fid or "")
                    display = [d.property_name for d in deals]
                    return gr.update(choices=display,
                                     value=display[0] if display else None)

                def _get_deal_id_from_name(fid, dname):
                    for deal in global_store.get_deals_for_fund(fid or ""):
                        if deal.property_name == dname:
                            return deal.deal_id
                    return dname

                ce_fund_dd.change(_update_ce_deals,
                                  inputs=[ce_fund_dd], outputs=[ce_deal_dd])

                def _ce_rows(fid, deal_name):
                    did = _get_deal_id_from_name(fid, deal_name)
                    if not fid or not did:
                        return []
                    cfs = sorted(
                        global_store.get_cashflows(fund_id=fid, deal_id=did),
                        key=lambda c: c.cash_date,
                    )
                    rows = []
                    for c in cfs:
                        fname = (global_store.funds[fid].fund_name
                                 if fid in global_store.funds else fid)
                        dname_disp = (global_store.deals[did].property_name
                                      if did in global_store.deals else did)
                        rows.append([
                            c.cash_date, fname, dname_disp,
                            _CF_LABEL.get(c.cf_type, c.cf_type),
                            f"${c.fund_amt:,.4f}M",
                        ])
                    return rows

                def add_cf(fid, deal_name, cdate, txn_type, fund_amount):
                    did = _get_deal_id_from_name(fid, deal_name)
                    if not all([fid, did, cdate, txn_type]):
                        return "Error: Fund, Deal, Date and Type required", []
                    type_map = {
                        "Investment":    "contribution",
                        "Current Income": "income",
                        "Disposition":   "disposition",
                    }
                    cf_type  = type_map.get(txn_type, "income")
                    amt      = fund_amount or 0.0
                    existing = global_store.get_cashflows(fund_id=fid, deal_id=did)
                    global_store.add_cashflow(Cashflow(
                        cashflow_id=f"{did}_{fid}_{len(existing)+1}",
                        deal_id=did, fund_id=fid, cash_date=cdate,
                        cf_type=cf_type, fund_amt=amt,
                    ))
                    return (
                        f"Added — ${amt:.4f}M  [{_CF_LABEL[cf_type]}]",
                        _ce_rows(fid, deal_name),
                    )

                ce_add_btn.click(add_cf,
                    inputs=[ce_fund_dd, ce_deal_dd, ce_date, ce_type, ce_amt],
                    outputs=[ce_status, ce_ledger])
                ce_view_btn.click(
                    lambda fid, dname: _ce_rows(fid, dname),
                    inputs=[ce_fund_dd, ce_deal_dd],
                    outputs=ce_ledger)

                # ── Cashflow Bulk Upload ───────────────────────────────────
                def process_cf_upload(file_obj):
                    if file_obj is None:
                        return "No file selected", []
                    filepath = (getattr(file_obj, 'path', None)
                                or getattr(file_obj, 'name', None)
                                or str(file_obj))
                    cfs_data, err = parse_cashflow_upload(filepath)
                    if err:
                        return f"Error: {err}", []

                    cfs_data.sort(key=lambda r: r.get('date', ''))
                    added, skipped = 0, 0
                    type_map = {
                        'Investment':    'contribution',
                        'Current Income': 'income',
                        'Disposition':   'disposition',
                    }
                    for row in cfs_data:
                        fname = row['fund_name']
                        dname = row['deal_name']
                        fund = next((f for f in global_store.funds.values()
                                     if f.fund_name == fname), None)
                        if not fund:
                            skipped += 1
                            continue
                        did = re.sub(r'[^a-z0-9]+', '_', dname.lower()).strip('_')
                        if did not in global_store.deals:
                            global_store.add_deal(Deal(
                                deal_id=did, property_name=dname,
                                sector='', location='',
                            ))
                        fid     = fund.fund_id
                        txn     = row['txn_type']
                        date    = row['date']
                        amt     = row.get('fund_amt') or 0.0
                        cf_type = type_map.get(txn)
                        if not cf_type:
                            skipped += 1
                            continue
                        existing = global_store.get_cashflows(fund_id=fid, deal_id=did)
                        global_store.add_cashflow(Cashflow(
                            cashflow_id=f"{did}_{fid}_{len(existing)+1}",
                            deal_id=did, fund_id=fid, cash_date=date,
                            cf_type=cf_type, fund_amt=amt,
                        ))
                        added += 1

                    return (
                        f"Imported {added} cashflow record(s). "
                        + (f"{skipped} row(s) skipped." if skipped else ""),
                        [],
                    )

                ce_dl_btn.click(generate_cashflow_template, outputs=[ce_dl_file])
                ce_dl_btn.click(lambda: gr.update(visible=True), outputs=[ce_dl_file])
                ce_ul_btn.click(
                    process_cf_upload,
                    inputs=[ce_ul_file],
                    outputs=[ce_ul_status, ce_ledger],
                )

            # ════════════════════════════════════════════════════════════════
            # Tab 7 — Quarterly NAV Entry (deal-level → fund auto-computed)
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("📅 Quarterly NAV"):
                gr.HTML("""
                <div style="background:#0f3460;border-left:4px solid #10b981;
                            padding:14px 18px;border-radius:8px;margin-bottom:14px;">
                  <p style="color:#e2e8f0;font-weight:700;font-size:14px;margin:0 0 6px;">
                    Property-Level Appraiser NAV Entry
                  </p>
                  <p style="color:#94a3b8;font-size:13px;margin:0;line-height:1.7;">
                    Enter the appraiser-reported value for <b style="color:#cbd5e1;">each property</b>
                    individually.<br>
                    Fund Ending NAV = <b style="color:#86efac;">Σ (property value × ownership %)</b>
                    — auto-computed, never typed manually.<br>
                    Beginning NAV and reporting period are set per fund below.
                  </p>
                </div>
                """)

                # ── Step 1: Set reporting period + beginning NAV per fund ──
                gr.HTML("""<p style="color:#e2e8f0;font-weight:700;font-size:14px;
                            margin:12px 0 8px;">Step 1 — Set Reporting Period & Beginning NAV per Fund</p>""")
                with gr.Row():
                    qi_nav_fund = gr.Dropdown(choices=[], label="Fund", scale=2)
                    qi_nav_rpt  = gr.Textbox(label="Quarter End Date",
                                              placeholder="2024-12-31", scale=1)
                    qi_nav_nps  = gr.Textbox(label="Quarter Start Date",
                                              placeholder="2024-01-01", scale=1)
                    qi_begin_nav = gr.Number(label="Beginning NAV (USD M) — prior quarter close",
                                             value=None, scale=2)
                    qi_period_btn = gr.Button("Save Period", variant="secondary", scale=1)
                qi_period_status = gr.Textbox(label="", interactive=False, show_label=False)

                def save_period(fid, rdate, nps, bnav):
                    if not fid or fid not in global_store.funds:
                        return "Error: select a valid fund"
                    f = global_store.funds[fid]
                    global_store.add_fund(Fund(
                        fund_id=f.fund_id, fund_name=f.fund_name,
                        reporting_date=rdate or f.reporting_date,
                        nav_period_start=nps or f.nav_period_start,
                        beginning_nav=bnav if bnav is not None else f.beginning_nav,
                        ending_nav=f.ending_nav,
                    ))
                    return f"Period saved for {f.fund_name}: {nps} → {rdate}, Beg NAV = ${bnav or f.beginning_nav:.2f}M"

                qi_period_btn.click(save_period,
                    inputs=[qi_nav_fund, qi_nav_rpt, qi_nav_nps, qi_begin_nav],
                    outputs=qi_period_status)

                gr.HTML("<hr style='border-color:#1e293b;margin:16px 0 12px'>")

                # ── Step 2: Enter 100% appraiser NAV per property (deal-level) ──
                gr.HTML("""
                <p style="color:#e2e8f0;font-weight:700;font-size:14px;margin:0 0 4px;">
                  Step 2 — Enter 100% Appraiser NAV per Property (deal-level, entered once)
                </p>
                <p style="color:#94a3b8;font-size:12px;margin:0 0 10px;">
                  Enter the appraiser-reported <b style="color:#cbd5e1;">full property value</b> once.
                  Each fund's share is computed automatically: <b style="color:#86efac;">fund NAV = property value × ownership %</b>.
                  All fund NAVs update simultaneously.
                </p>""")

                with gr.Row():
                    qi_deal_dd  = gr.Dropdown(
                        choices=[], label="Property (Deal)", scale=3)
                    qi_appr_nav = gr.Number(
                        label="100% Appraiser NAV — full property value (USD M)",
                        value=None, scale=2)
                    qi_deal_btn = gr.Button("Save & Recompute All Fund NAVs",
                                            variant="primary", scale=2)
                qi_deal_status = gr.Textbox(label="", interactive=False, show_label=False)

                # Populate deal dropdown from ALL deals in store
                def _all_deals_choices():
                    return [d.property_name for d in global_store.deals.values()]

                def save_deal_nav(deal_name, appr_nav):
                    if not deal_name:
                        return "Error: select a property", fund_snapshot()
                    if appr_nav is None or appr_nav <= 0:
                        return "Error: enter a positive appraiser NAV", fund_snapshot()
                    deal = next((d for d in global_store.deals.values()
                                 if d.property_name == deal_name), None)
                    if not deal:
                        return "Error: deal not found", fund_snapshot()
                    # Save 100% appraiser NAV on the deal itself
                    global_store.add_deal(deal.model_copy(update={"appraiser_nav": appr_nav}))
                    # Recompute ALL funds that hold this deal
                    global_store.sync_all_fund_navs()
                    # Build allocation summary
                    owners = [o for o in global_store.ownerships if o.deal_id == deal.deal_id]
                    lines  = [f"{global_store.funds[o.fund_id].fund_name}: "
                               f"{o.ownership_pct*100:.0f}% × ${appr_nav:.2f}M = "
                               f"${appr_nav * o.ownership_pct:.2f}M"
                               for o in owners if o.fund_id in global_store.funds]
                    return (
                        f"Saved: {deal_name} = ${appr_nav:.2f}M (100%).\n"
                        + "  |  ".join(lines)
                        + "\nAll fund NAVs recomputed.",
                        fund_snapshot(),
                    )

                # Placeholder — qi_deal_fund is used only in refresh_dropdowns
                qi_deal_fund = gr.Dropdown(choices=[], visible=False)

                gr.HTML("<hr style='border-color:#1e293b;margin:16px 0 12px'>")

                # ── Snapshot ──────────────────────────────────────────────
                gr.HTML("""<p style="color:#e2e8f0;font-weight:700;font-size:14px;
                            margin:0 0 8px;">Fund Snapshot — auto-computed Ending NAV</p>""")
                qi_snap_refresh = gr.Button("Refresh Snapshot", variant="secondary")
                qi_snapshot = gr.Dataframe(
                    headers=["Fund", "Period", "Beginning NAV",
                             "Ending NAV (auto)", "# Properties", "Write Up/Down"],
                    datatype=["str"]*6, column_count=6, label="",
                )

                def fund_snapshot():
                    rows = []
                    for fid, f in global_store.funds.items():
                        try:
                            bridge = compute_nav_bridge(fid, global_store)
                            wud = bridge.get("write_up_down", 0.0)
                        except Exception:
                            wud = 0.0
                        n_deals = len(global_store.get_deals_for_fund(fid))
                        period  = f"{f.nav_period_start or '—'} → {f.reporting_date or '—'}"
                        rows.append([
                            f.fund_name, period,
                            f"${f.beginning_nav:.2f}M",
                            f"${f.ending_nav:.2f}M",
                            str(n_deals),
                            f"${wud:.4f}M",
                        ])
                    return rows

                # Wire save_deal_nav output to snapshot
                qi_deal_btn.click(save_deal_nav,
                    inputs=[qi_deal_dd, qi_appr_nav],
                    outputs=[qi_deal_status, qi_snapshot])
                qi_snap_refresh.click(fund_snapshot, outputs=qi_snapshot)
                qi_period_btn.click(fund_snapshot, outputs=qi_snapshot)
                # Refresh deal dropdown when dataset is loaded
                load_btn.click(
                    lambda: gr.update(choices=_all_deals_choices()),
                    outputs=[qi_deal_dd]
                )

            # ════════════════════════════════════════════════════════════════
            # Tab 8 — Export / Answer Key
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("📥 Export & Verify"):
                gr.HTML("""
                <div style="background:#1e3a5f;border-left:4px solid #10b981;
                            padding:14px 18px;border-radius:8px;margin-bottom:16px;">
                  <p style="color:#e2e8f0;font-weight:700;font-size:14px;margin:0 0 6px;">
                    📥 Answer Key Export — Reconcile in your Excel
                  </p>
                  <p style="color:#94a3b8;font-size:13px;margin:0;line-height:1.7;">
                    Downloads an Excel with the system-computed NAV Bridge and metrics
                    for every fund in the DB.<br>
                    Each fund gets its own sheet: raw cashflows → 8-line bridge →
                    MOIC → IRR, with formulas explained so you can verify manually.
                  </p>
                </div>
                """)
                export_btn  = gr.Button("⬇  Download Answer Key (.xlsx)",
                                        variant="primary", size="lg")
                export_file = gr.File(label="Your answer key is ready", visible=False)
                export_status = gr.Textbox(label="", interactive=False, show_label=False)

                def do_export():
                    if not global_store.funds:
                        return "No funds in database yet.", gr.update(visible=False)
                    path = export_answer_key(global_store)
                    return (
                        f"Exported {len(global_store.funds)} fund(s). "
                        "Download the file and open in Excel to reconcile.",
                        gr.update(value=path, visible=True),
                    )

                export_btn.click(do_export, outputs=[export_status, export_file])

            # ════════════════════════════════════════════════════════════════
            # Tab 9 — AI Test Run
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("🤖 AI Test Run"):
                gr.HTML("""
                <div style="background:#1e3a5f;border-left:4px solid #a855f7;
                            padding:14px 18px;border-radius:8px;margin-bottom:16px;">
                  <p style="color:#e2e8f0;font-weight:700;font-size:14px;margin:0 0 6px;">
                    🤖 Run the AI Agent — See What It Gets Right and Wrong
                  </p>
                  <p style="color:#94a3b8;font-size:13px;margin:0;line-height:1.7;">
                    Enter your OpenAI API key, pick a task, and click Run.<br>
                    The AI will call our tools step-by-step, then submit its answers.<br>
                    You will see a side-by-side comparison: <b style="color:#86efac;">AI's answer</b>
                    vs <b style="color:#93c5fd;">correct answer</b>, with pass/fail per line.
                  </p>
                </div>
                """)

                with gr.Row():
                    ai_api_key  = gr.Textbox(
                        label="API Key", placeholder="sk-...",
                        type="password", scale=3,
                    )
                    ai_base_url = gr.Textbox(
                        label="API Base URL", value="https://api.openai.com/v1", scale=3,
                    )
                    ai_model    = gr.Textbox(
                        label="Model", value="gpt-4o-mini", scale=2,
                    )

                with gr.Row():
                    ai_level = gr.Radio(
                        choices=["Portfolio", "Fund", "Investment/Deal"],
                        value="Fund",
                        label="Analysis Level",
                        scale=3,
                    )
                    ai_task  = gr.Dropdown(
                        choices=["easy", "medium", "hard"], value="easy",
                        label="Difficulty (grading mode)", scale=1,
                    )

                with gr.Row():
                    ai_fund_dd = gr.Dropdown(choices=[], label="Fund", scale=2,
                                             visible=True)
                    ai_deal_dd = gr.Dropdown(
                        choices=["(whole fund)"], value="(whole fund)",
                        label="Investment/Deal", scale=3,
                        visible=False,   # hidden until Investment/Deal level selected
                    )

                with gr.Row():
                    ai_run_btn = gr.Button("▶  Run AI Agent", variant="primary", scale=2)
                    ai_reward  = gr.Textbox(label="Final Score", interactive=False, scale=2)

                def _get_ai_seed_store():
                    from fundlens.server.data_store import DataStore as _DS
                    s = _DS()
                    load_hard_task(s)
                    return s

                def _refresh_ai_dropdowns():
                    s = _get_ai_seed_store()
                    fund_ids = list(s.funds.keys())
                    fv = fund_ids[0] if fund_ids else None
                    return gr.update(choices=fund_ids, value=fv), gr.update(choices=["(whole fund)"])

                def _update_ai_deals(fid):
                    if not fid:
                        return gr.update(choices=["(whole fund)"], value="(whole fund)")
                    s = _get_ai_seed_store()
                    deals = ["(whole fund)"] + [d.deal_id for d in s.get_deals_for_fund(fid)]
                    return gr.update(choices=deals, value=deals[1] if len(deals) > 1 else deals[0])

                ai_fund_dd.change(_update_ai_deals, inputs=[ai_fund_dd], outputs=[ai_deal_dd])

                def _toggle_ai_dropdowns(lvl):
                    show_fund = lvl in ("Fund", "Investment/Deal")
                    show_deal = lvl == "Investment/Deal"
                    return gr.update(visible=show_fund), gr.update(visible=show_deal)

                ai_level.change(
                    _toggle_ai_dropdowns, inputs=[ai_level],
                    outputs=[ai_fund_dd, ai_deal_dd],
                )

                gr.HTML("""
                <div style="font-size:12px;color:#64748b;margin:6px 0;">
                  ✔ Pass = within tolerance &nbsp;|&nbsp; ✗ Fail = too far off &nbsp;|&nbsp; ✗ Missing = AI never submitted
                </div>""")

                ai_comparison = gr.Dataframe(
                    headers=["Line Item", "AI's Answer", "Correct Answer", "Result"],
                    datatype=["str"] * 4, column_count=4,
                    label="Answer Comparison — AI vs Correct",
                    wrap=True,
                )
                ai_log = gr.Textbox(
                    label="Step-by-Step Log (what the AI did)",
                    interactive=False, lines=16, max_lines=30,
                )

                def _run_with_selection(api_key, base_url, model, task, lvl, fund, deal):
                    deal_val = "" if deal in ("(whole fund)", "") else deal
                    return _run_ai_test(api_key, base_url, model, task, lvl, fund, deal_val)

                ai_run_btn.click(
                    _run_with_selection,
                    inputs=[ai_api_key, ai_base_url, ai_model, ai_task,
                            ai_level, ai_fund_dd, ai_deal_dd],
                    outputs=[ai_log, ai_comparison, ai_reward],
                )

            # ════════════════════════════════════════════════════════════════
            # Tab 10 — Answer Key
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("📋 Answer Key"):
                gr.HTML("""
                <div style="background:#1e3a5f;border-left:4px solid #10b981;
                            padding:14px 18px;border-radius:8px;margin-bottom:16px;">
                  <p style="color:#e2e8f0;font-weight:700;font-size:14px;margin:0 0 6px;">
                    📋 Answer Key — Correct Values vs AI Submission
                  </p>
                  <p style="color:#94a3b8;font-size:13px;margin:0;line-height:1.7;">
                    Select a level and fund/deal to see the correct answers our system has computed.<br>
                    After running the AI Test, come back here to see the one-to-one comparison.
                  </p>
                </div>
                """)

                with gr.Row():
                    ak_level   = gr.Radio(
                        choices=["Portfolio", "Fund", "Investment/Deal"],
                        value="Fund", label="Level", scale=3,
                    )
                    ak_fund_dd = gr.Dropdown(choices=[], label="Fund", scale=2,
                                             visible=True)
                    ak_deal_dd = gr.Dropdown(
                        choices=["(whole fund)"], value="(whole fund)",
                        label="Investment/Deal", scale=2,
                        visible=False,
                    )

                with gr.Row():
                    ak_show_btn    = gr.Button("Show Correct Answers", variant="secondary", scale=1)
                    ak_compare_btn = gr.Button("Compare vs Last AI Run", variant="primary", scale=1)

                gr.Markdown("#### NAV Bridge — Correct Answers")
                ak_bridge_tbl = gr.Dataframe(
                    headers=["Line Item", "Correct Value"],
                    datatype=["str", "str"], column_count=2,
                    label="", wrap=True,
                )

                gr.Markdown("#### Metrics — Correct Answers")
                ak_metrics_tbl = gr.Dataframe(
                    headers=["Metric", "Correct Value"],
                    datatype=["str", "str"], column_count=2,
                    label="", wrap=True,
                )

                gr.Markdown("#### One-to-One Comparison  (correct vs what AI submitted)")
                ak_compare_tbl = gr.Dataframe(
                    headers=["Line Item", "AI's Answer", "Correct Answer", "Pass/Fail"],
                    datatype=["str"] * 4, column_count=4,
                    label="", wrap=True,
                )

                def _update_ak_deals(fid):
                    if not fid:
                        return gr.update(choices=["(whole fund)"])
                    deals = ["(whole fund)"] + [d.deal_id for d in global_store.get_deals_for_fund(fid)]
                    return gr.update(choices=deals, value=deals[0])

                ak_fund_dd.change(_update_ak_deals, inputs=[ak_fund_dd], outputs=[ak_deal_dd])

                def _toggle_ak_dropdowns(lvl):
                    show_fund = lvl in ("Fund", "Investment/Deal")
                    show_deal = lvl == "Investment/Deal"
                    return gr.update(visible=show_fund), gr.update(visible=show_deal)

                ak_level.change(
                    _toggle_ak_dropdowns, inputs=[ak_level],
                    outputs=[ak_fund_dd, ak_deal_dd],
                )

                def _ak_show(level, fund, deal):
                    deal_val = "" if deal in ("(whole fund)", "") else deal
                    bridge_rows, metrics_rows = _correct_answer_rows(level, fund, deal_val)
                    return bridge_rows, metrics_rows

                def _ak_compare(level, fund, deal):
                    deal_val = "" if deal in ("(whole fund)", "") else deal
                    rows = _comparison_rows(level, fund, deal_val)
                    if not rows:
                        return [["No AI test run yet — use the 🤖 AI Test Run tab first", "", "", ""]]
                    return rows

                ak_show_btn.click(
                    _ak_show,
                    inputs=[ak_level, ak_fund_dd, ak_deal_dd],
                    outputs=[ak_bridge_tbl, ak_metrics_tbl],
                )
                ak_compare_btn.click(
                    _ak_compare,
                    inputs=[ak_level, ak_fund_dd, ak_deal_dd],
                    outputs=[ak_compare_tbl],
                )

        # ── Dynamic dropdowns — refresh after seed load ────────────────────
        def refresh_dropdowns():
            fund_ids   = list(global_store.funds.keys())
            fund_names = [f.fund_name for f in global_store.funds.values()]
            fv   = fund_ids[0] if fund_ids else None
            fnv  = fund_names[0] if fund_names else None
            fu   = gr.update(choices=fund_ids,   value=fv)
            fnu  = gr.update(choices=fund_names,  value=fnv)
            return fu, fu, fu, fnu, fu, fu, fu

        load_btn.click(
            refresh_dropdowns,
            outputs=[bridge_fund, deals_fund, cf_fund_view,
                     ob_ifund,
                     ce_fund_dd,
                     qi_nav_fund, qi_deal_fund],
        )
        load_btn.click(
            _refresh_ai_dropdowns,
            outputs=[ai_fund_dd, ai_deal_dd],
        )
        load_btn.click(
            lambda: (_ob_fund_rows(), _ob_inv_rows()),
            outputs=[ob_ftbl, ob_itbl],
        )

        # ── Auto-restore on page load / browser refresh ────────────────────
        def _refresh_ak_dropdowns():
            fund_ids = list(global_store.funds.keys())
            deal_ids = ["(whole fund)"] + list(global_store.deals.keys())
            fv = fund_ids[0] if fund_ids else None
            return gr.update(choices=fund_ids, value=fv), gr.update(choices=deal_ids)

        load_btn.click(_refresh_ak_dropdowns, outputs=[ak_fund_dd, ak_deal_dd])

        def _on_page_load():
            fund_ids   = list(global_store.funds.keys())
            fund_names = [f.fund_name for f in global_store.funds.values()]
            deal_names = [d.property_name for d in global_store.deals.values()]
            deal_ids   = ["(whole fund)"] + list(global_store.deals.keys())
            fv  = fund_ids[0]   if fund_ids   else None
            fnv = fund_names[0] if fund_names else None
            fu  = gr.update(choices=fund_ids,  value=fv)
            fnu = gr.update(choices=fund_names, value=fnv)
            fdu = gr.update(choices=deal_names, value=deal_names[0] if deal_names else None)
            fu_shared = gr.update(choices=fund_ids, value=fv)
            fd_shared = gr.update(choices=deal_ids)
            return (
                _portfolio_table(),
                _ob_fund_rows(),
                _ob_inv_rows(),
                fu, fu, fu, fnu, fu, fu, fdu,
                fu_shared, fd_shared,   # ai_fund_dd, ai_deal_dd
                fu_shared, fd_shared,   # ak_fund_dd, ak_deal_dd
            )

        demo.load(
            _on_page_load,
            outputs=[
                portfolio_table, ob_ftbl, ob_itbl,
                bridge_fund, deals_fund, cf_fund_view,
                ob_ifund, ce_fund_dd, qi_nav_fund, qi_deal_dd,
                ai_fund_dd, ai_deal_dd,
                ak_fund_dd, ak_deal_dd,
            ],
        )

    return demo

"""
FundLens Investor Portal — Raj's view.
Read-only. Plain English. No data entry.
Mounts at /investor.
"""
from __future__ import annotations
import gradio as gr
from fundlens.server.data_store import store as global_store
from fundlens.server.calculations import compute_nav_bridge, compute_metrics


# ── Mode detection ─────────────────────────────────────────────────────────

def _detect_mode() -> str:
    """Infer which scenario is loaded from the set of fund IDs in the store."""
    ids = set(global_store.funds.keys())
    if not ids:
        return "none"
    if "gamma" in ids:
        return "hard"
    if "beta" in ids:
        return "medium"
    if "alpha" in ids:
        return "easy"
    return "unknown"


_MODE_META = {
    "none":    {"label": "No data loaded",   "color": "#6b7280", "border": "#374151",
                "graded": "Load a scenario in the Admin portal first."},
    "easy":    {"label": "Easy Mode",        "color": "#3b82f6", "border": "#1d4ed8",
                "graded": "Graded: NAV Bridge only (8 line items)"},
    "medium":  {"label": "Medium Mode",      "color": "#f59e0b", "border": "#d97706",
                "graded": "Graded: NAV Bridge + MOIC"},
    "hard":    {"label": "Hard Mode",        "color": "#10b981", "border": "#059669",
                "graded": "Graded: NAV Bridge + MOIC + IRR  (3 funds, co-investment)"},
    "unknown": {"label": "Custom data",      "color": "#8b5cf6", "border": "#6d28d9",
                "graded": ""},
}

_METRIC_AVAILABILITY = {
    "moic": {"easy": False, "medium": True,  "hard": True},
    "irr":  {"easy": False, "medium": False, "hard": True},
}


# ── Plain-English helpers ──────────────────────────────────────────────────

def _moic_label(moic: float, mode: str) -> str:
    if moic <= 0 or not _METRIC_AVAILABILITY["moic"].get(mode, True):
        return _na_badge("moic", mode)
    if moic >= 2.5:
        return f"{moic:.2f}x  ★ Strong outperformance"
    elif moic >= 2.0:
        return f"{moic:.2f}x  ✔ Good return"
    elif moic >= 1.5:
        return f"{moic:.2f}x  → Moderate return"
    elif moic >= 1.0:
        return f"{moic:.2f}x  ⚠ Capital returned, limited gain"
    else:
        return f"{moic:.2f}x  ✘ Capital loss"


def _irr_label(irr: float, mode: str) -> str:
    if irr <= 0 or not _METRIC_AVAILABILITY["irr"].get(mode, True):
        return _na_badge("irr", mode)
    pct = irr * 100
    if pct >= 20:
        return f"{pct:.1f}%  ★ Excellent annual return"
    elif pct >= 12:
        return f"{pct:.1f}%  ✔ Good annual return"
    elif pct >= 8:
        return f"{pct:.1f}%  → In line with market"
    elif pct >= 0:
        return f"{pct:.1f}%  ⚠ Below target"
    else:
        return f"{pct:.1f}%  ✘ Negative return"


def _na_badge(metric: str, mode: str) -> str:
    """Human-friendly 'not available' message for a metric in the given mode."""
    if mode == "none":
        return "— (no data loaded)"
    available_from = {"moic": "Medium", "irr": "Hard"}
    return f"— (available in {available_from.get(metric, '?')} mode and above)"


def _nav_change_label(beg: float, end: float) -> str:
    if beg == 0:
        return f"—  →  ${end:.1f}M"
    change = end - beg
    pct    = change / beg * 100
    sign   = "+" if change >= 0 else ""
    return f"${beg:.1f}M  →  ${end:.1f}M  ({sign}{pct:.1f}% this period)"


# ── Mode status HTML ───────────────────────────────────────────────────────

def _mode_banner_html() -> str:
    mode = _detect_mode()
    meta = _MODE_META.get(mode, _MODE_META["unknown"])
    return f"""
    <div style="display:flex; align-items:center; gap:12px; padding:10px 18px;
                background:#1e293b; border:1px solid {meta['border']};
                border-radius:8px; margin-bottom:12px;">
      <span style="background:{meta['color']}; color:#fff; font-size:11px;
                   font-weight:700; padding:3px 10px; border-radius:20px; white-space:nowrap;">
        {meta['label'].upper()}
      </span>
      <span style="color:#cbd5e1; font-size:13px;">{meta['graded']}</span>
    </div>
    """


# ── Data builders ─────────────────────────────────────────────────────────

def _fund_overview():
    """Top-level fund cards data + updated mode banner."""
    mode = _detect_mode()
    rows = []
    for fid, fund in global_store.funds.items():
        m = compute_metrics(fid, global_store)
        rows.append([
            fund.fund_name,
            _nav_change_label(fund.beginning_nav, fund.ending_nav),
            _moic_label(m.get("moic", 0), mode),
            _irr_label(m.get("irr", 0), mode),
        ])
    if not rows:
        rows = [["No funds loaded", "Load a scenario in the Admin portal", "—", "—"]]
    return rows, _mode_banner_html()


def _nav_walk_table(fund_id: str):
    """8-line NAV bridge with plain-English explanation column."""
    if fund_id not in global_store.funds:
        return []
    bridge = compute_nav_bridge(fund_id, global_store)
    explanations = {
        "beginning_nav":         "Where the fund started this period",
        "contribution":          "New capital called from investors",
        "disposition":           "Proceeds received from property sales",
        "income":                "Rent and yield collected",
        "cashflow_adjusted_nav": "NAV after all cash movements",
        "income_reversal":       "Income added back (already counted in valuation)",
        "write_up_down":         "Change in property values (appraiser estimate)",
        "ending_nav":            "Fund value at end of period",
    }
    labels = {
        "beginning_nav":         "Opening Value",
        "contribution":          "(+) Capital Called",
        "disposition":           "(−) Sales Proceeds",
        "income":                "(+) Income Received",
        "cashflow_adjusted_nav": "= Cash-Adjusted Value",
        "income_reversal":       "(−) Income Reversal",
        "write_up_down":         "(+/−) Property Value Change",
        "ending_nav":            "= Closing Value",
    }
    rows = []
    for k, v in bridge.items():
        rows.append([labels.get(k, k), f"${v:,.2f}M", explanations.get(k, "")])
    return rows


def _itd_summary(fund_id: str):
    """Inception-to-date cashflow summary."""
    if fund_id not in global_store.funds:
        return []
    fund = global_store.funds[fund_id]
    cfs  = global_store.get_cashflows(fund_id=fund_id)

    total_in   = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
    total_disp = sum(c.fund_amt for c in cfs if c.cf_type == "disposition")
    total_inc  = sum(c.fund_amt for c in cfs if c.cf_type == "income")
    total_out  = total_disp + total_inc
    unrealized = fund.ending_nav

    return [
        ["Total Capital Invested (ITD)",   f"${total_in:.2f}M",   "All capital calls since fund inception"],
        ["Total Cash Received (ITD)",      f"${total_disp:.2f}M", "Property sale proceeds returned to investors"],
        ["Total Income Received (ITD)",    f"${total_inc:.2f}M",  "Rent and distributions paid out"],
        ["Total Cash Returned (ITD)",      f"${total_out:.2f}M",  "Sales + Income combined"],
        ["Current Fund Value (Unrealized)",f"${unrealized:.2f}M", "Appraiser-estimated value of remaining properties"],
        ["Total Value (Cash + Unrealized)",f"${total_out + unrealized:.2f}M",
         "What investors have received + what remains invested"],
    ]


def _deals_by_fund(fund_id: str):
    rows = []
    for deal in global_store.get_deals_for_fund(fund_id):
        own  = global_store.get_ownership(fund_id, deal.deal_id)
        cfs  = global_store.get_cashflows(fund_id=fund_id, deal_id=deal.deal_id)
        inv  = sum(abs(c.fund_amt) for c in cfs if c.cf_type == "contribution")
        disp = sum(c.fund_amt for c in cfs if c.cf_type == "disposition")
        inc  = sum(c.fund_amt for c in cfs if c.cf_type == "income")
        rows.append([
            deal.property_name,
            deal.sector,
            deal.location,
            f"{(own.ownership_pct * 100):.0f}%" if own else "100%",
            f"${inv:.2f}M",
            f"${disp + inc:.2f}M",
        ])
    return rows


# ── UI ────────────────────────────────────────────────────────────────────

def build_investor_ui() -> gr.Blocks:
    with gr.Blocks(title="FundLens — Investor Portal") as demo:

        gr.HTML("""
        <div style="background: linear-gradient(135deg, #0f3460 0%, #16213e 60%, #1a1a2e 100%);
                    padding: 28px 36px; border-radius: 14px; margin-bottom: 16px;">
            <h1 style="color: #e2e8f0; margin: 0; font-size: 28px; font-weight: 700;">
                🏢 FundLens — Investor Portal
            </h1>
            <p style="color: #94a3b8; margin: 6px 0 0 0; font-size: 14px;">
                Real-time fund performance &nbsp;·&nbsp; Inception-to-date reporting
                &nbsp;·&nbsp; Read-only view
            </p>
        </div>
        """)

        # ── Mode banner (live) ────────────────────────────────────────────
        mode_banner = gr.HTML(_mode_banner_html())

        # ── Metric explainer cards ────────────────────────────────────────
        gr.HTML("""
        <div style="display:flex; gap:12px; margin-bottom:16px; flex-wrap:wrap;">
          <div style="flex:1; min-width:200px; background:#1e3a5f; border-left:4px solid #3b82f6;
                      padding:14px 18px; border-radius:8px;">
            <p style="color:#93c5fd; font-weight:700; margin:0 0 4px; font-size:13px;">
              MOIC &nbsp;<span style="background:#f59e0b;color:#000;font-size:10px;
              padding:1px 6px;border-radius:10px;font-weight:600;">Medium &amp; Hard</span>
            </p>
            <p style="color:#e2e8f0; margin:0; font-size:13px; line-height:1.5;">
              <b>Multiple on Invested Capital</b><br>
              For every $1 you put in, how many $ are you getting back?<br>
              <span style="color:#86efac;">2.0x = doubled your money</span>
            </p>
          </div>
          <div style="flex:1; min-width:200px; background:#1e3a5f; border-left:4px solid #10b981;
                      padding:14px 18px; border-radius:8px;">
            <p style="color:#6ee7b7; font-weight:700; margin:0 0 4px; font-size:13px;">
              IRR &nbsp;<span style="background:#10b981;color:#fff;font-size:10px;
              padding:1px 6px;border-radius:10px;font-weight:600;">Hard only</span>
            </p>
            <p style="color:#e2e8f0; margin:0; font-size:13px; line-height:1.5;">
              <b>Internal Rate of Return</b><br>
              The annual growth rate of your investment, accounting for timing.<br>
              <span style="color:#86efac;">20%+ = excellent for real estate PE</span>
            </p>
          </div>
          <div style="flex:1; min-width:200px; background:#1e3a5f; border-left:4px solid #f59e0b;
                      padding:14px 18px; border-radius:8px;">
            <p style="color:#fcd34d; font-weight:700; margin:0 0 4px; font-size:13px;">
              NAV Walk &nbsp;<span style="background:#3b82f6;color:#fff;font-size:10px;
              padding:1px 6px;border-radius:10px;font-weight:600;">All modes</span>
            </p>
            <p style="color:#e2e8f0; margin:0; font-size:13px; line-height:1.5;">
              <b>Net Asset Value Bridge</b><br>
              Step-by-step explanation of how the fund value moved this period.
            </p>
          </div>
        </div>
        """)

        with gr.Tabs():

            # ════════════════════════════════════════════════════════════════
            # Tab 1 — Portfolio Overview
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("📊 Portfolio Overview"):
                gr.Markdown(
                    "### All Funds — Performance at a Glance\n"
                    "MOIC and IRR show **'— (available in X mode)'** when the current "
                    "scenario does not grade that metric."
                )
                refresh_btn = gr.Button("Refresh", variant="secondary", size="sm")
                overview_table = gr.Dataframe(
                    headers=["Fund", "NAV Movement (this period)", "MOIC", "IRR"],
                    datatype=["str"] * 4, column_count=4,
                    label="",
                    wrap=True,
                )
                refresh_btn.click(
                    _fund_overview,
                    outputs=[overview_table, mode_banner],
                )

            # ════════════════════════════════════════════════════════════════
            # Tab 2 — NAV Walk
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("📋 NAV Walk"):
                gr.Markdown(
                    "### How did the fund value change this period?\n"
                    "This table walks through every step from opening value to closing value. "
                    "**Graded in all modes.**"
                )
                with gr.Row():
                    nav_fund_dd = gr.Dropdown(choices=[], label="Select Fund", scale=2)
                    nav_btn     = gr.Button("Show NAV Walk", variant="primary", scale=1)

                nav_table = gr.Dataframe(
                    headers=["Step", "Amount", "What this means"],
                    datatype=["str"] * 3, column_count=3,
                    label="NAV Walk — Step by Step",
                    wrap=True,
                )
                nav_btn.click(_nav_walk_table, inputs=[nav_fund_dd], outputs=[nav_table])

            # ════════════════════════════════════════════════════════════════
            # Tab 3 — ITD Summary
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("📈 ITD Summary"):
                gr.Markdown(
                    "### Inception-to-Date Summary\n"
                    "Everything since the fund launched — how much went in, how much came back, "
                    "and what remains invested today."
                )
                with gr.Row():
                    itd_fund_dd = gr.Dropdown(choices=[], label="Select Fund", scale=2)
                    itd_btn     = gr.Button("Show Summary", variant="primary", scale=1)

                itd_table = gr.Dataframe(
                    headers=["Item", "Amount", "Explanation"],
                    datatype=["str"] * 3, column_count=3,
                    label="ITD Summary",
                    wrap=True,
                )
                itd_btn.click(_itd_summary, inputs=[itd_fund_dd], outputs=[itd_table])

            # ════════════════════════════════════════════════════════════════
            # Tab 4 — Properties
            # ════════════════════════════════════════════════════════════════
            with gr.Tab("🏗️ Properties"):
                gr.Markdown(
                    "### Properties in the Fund\n"
                    "Each property the fund has invested in, with your ownership share "
                    "and how much capital has moved."
                )
                with gr.Row():
                    prop_fund_dd = gr.Dropdown(choices=[], label="Select Fund", scale=2)
                    prop_btn     = gr.Button("Show Properties", variant="primary", scale=1)

                prop_table = gr.Dataframe(
                    headers=["Property", "Sector", "Location",
                             "Ownership", "Capital Invested", "Cash Returned"],
                    datatype=["str"] * 6, column_count=6,
                    label="",
                    wrap=True,
                )
                prop_btn.click(_deals_by_fund, inputs=[prop_fund_dd], outputs=[prop_table])

        # ── Auto-load on page open ─────────────────────────────────────────
        def _on_load():
            fund_ids = list(global_store.funds.keys())
            fv  = fund_ids[0] if fund_ids else None
            fu  = gr.update(choices=fund_ids, value=fv)
            tbl, banner = _fund_overview()
            return tbl, banner, fu, fu, fu

        demo.load(
            _on_load,
            outputs=[overview_table, mode_banner, nav_fund_dd, itd_fund_dd, prop_fund_dd],
        )

    return demo

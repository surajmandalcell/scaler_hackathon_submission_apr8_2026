const ENDPOINTS = [
  { method: "POST", path: "/reset", desc: "Initialize episode with task_id" },
  { method: "POST", path: "/step", desc: "Execute MCP tool call via CallToolAction" },
  { method: "GET",  path: "/state", desc: "Current episode state (task_id, is_done)" },
  { method: "GET",  path: "/health", desc: "Health check" },
  { method: "POST", path: "/api/load-scenario", desc: "Load seed data for UI display" },
  { method: "GET",  path: "/api/portfolio", desc: "Fund-level summary (NAV, MOIC, IRR)" },
  { method: "GET",  path: "/api/bridge/{fund_id}", desc: "8-line NAV bridge for a fund" },
  { method: "GET",  path: "/api/deals/{fund_id}", desc: "Deals, ownership, cashflows per deal" },
  { method: "GET",  path: "/api/cashflows/{fund_id}", desc: "Cashflow records + totals" },
  { method: "GET",  path: "/api/sectors", desc: "Sector-level breakdown across funds" },
];

const MCP_TOOLS = [
  { name: "get_available_filters", desc: "List fund_ids, deal_ids, sectors" },
  { name: "get_portfolio_summary", desc: "Fund-level NAV, MOIC, IRR" },
  { name: "get_nav_bridge", desc: "8-line NAV bridge for one fund" },
  { name: "get_irr", desc: "IRR for one fund" },
  { name: "compare_funds", desc: "Side-by-side fund comparison" },
  { name: "get_sector_report", desc: "Grouped by property sector" },
  { name: "get_deal_exposure", desc: "Deal across all holding funds" },
  { name: "get_raw_cashflows", desc: "Paginated cashflow records" },
  { name: "get_cashflow_summary", desc: "Pre-aggregated totals + IRR schedule" },
  { name: "get_deal_info", desc: "Property-level ownership, appraiser NAV" },
  { name: "get_portfolio_bridge", desc: "NAV bridge across all funds" },
  { name: "get_deal_bridge", desc: "NAV bridge for single deal" },
  { name: "get_deal_metrics", desc: "MOIC and IRR for single deal" },
  { name: "get_portfolio_metrics", desc: "Portfolio-wide MOIC and IRR" },
  { name: "submit_report", desc: "Grade submission, returns reward 0.0-1.0" },
];

const BRIDGE_FORMULA = [
  { line: "Beginning NAV",      formula: "Appraiser value at period start" },
  { line: "+ Contribution",     formula: "Sum of capital calls during period" },
  { line: "- Disposition",      formula: "Sum of sale proceeds during period" },
  { line: "+ Income",           formula: "Sum of rental/operating income during period" },
  { line: "= CF-Adjusted NAV",  formula: "Beginning + Contrib - Disp + Income" },
  { line: "- Income Reversal",  formula: "-Income (removed from valuation)" },
  { line: "+/- Write Up/Down",  formula: "Plug: Ending - (CF-Adj + Income Reversal)" },
  { line: "= Ending NAV",       formula: "Appraiser value at period end" },
];

const TOLERANCES = [
  { metric: "NAV bridge amounts", tolerance: "+/- $0.50M", example: "Correct 100.0 -> accept 99.50-100.50" },
  { metric: "MOIC (multiple)",    tolerance: "+/- 0.02x",  example: "Correct 1.50 -> accept 1.48-1.52" },
  { metric: "IRR",                tolerance: "+/- 1.0%",   example: "Correct 0.150 -> accept 0.140-0.160" },
];

const DIFFICULTIES = [
  { id: "easy",   desc: "RE Alpha Fund I - 3 properties, 100% owned. Compute 8-line NAV bridge.", graded: "Bridge only (8 items)" },
  { id: "medium", desc: "RE Beta Fund II - 5 properties including Data Center. Compute bridge + MOIC.", graded: "Bridge (60%) + MOIC (40%)" },
  { id: "hard",   desc: "Cross-fund portfolio - RE Alpha, Beta, Gamma with co-investment. Compute bridge + MOIC + IRR.", graded: "Bridge (50%) + MOIC + IRR (50%)" },
];

export default function DocsPage() {
  return (
    <div className="stack">
      <div className="section-header">
        <p className="eyebrow mono">05 -- Reference</p>
        <h2 className="serif section-title">Documentation</h2>
      </div>

      <div className="card card-accent-blue">
        <p className="metric-label">About</p>
        <p>
          FundLens is an OpenEnv environment that tests AI agents on real estate private equity
          fund reporting. Agents use MCP tools to query fund data, compute NAV bridges (8-line
          valuation walks), and report performance metrics (MOIC, IRR).
        </p>
      </div>

      <div className="stack">
        <div className="section-header">
          <p className="eyebrow mono">HTTP Endpoints</p>
        </div>
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Method</th>
                <th>Path</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {ENDPOINTS.map((e) => (
                <tr key={e.path}>
                  <td className="mono small">{e.method}</td>
                  <td className="mono small">{e.path}</td>
                  <td className="muted">{e.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="stack">
        <div className="section-header">
          <p className="eyebrow mono">MCP Tools (15 total)</p>
        </div>
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Tool Name</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {MCP_TOOLS.map((t) => (
                <tr key={t.name}>
                  <td className="mono small">{t.name}</td>
                  <td className="muted">{t.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="stack">
        <div className="section-header">
          <p className="eyebrow mono">NAV Bridge Formula</p>
        </div>
        <div className="card card-accent-emerald">
          <table className="data-table">
            <thead>
              <tr>
                <th>Line</th>
                <th>Computation</th>
              </tr>
            </thead>
            <tbody>
              {BRIDGE_FORMULA.map((b, i) => (
                <tr key={i}>
                  <td className="mono small">{b.line}</td>
                  <td className="muted">{b.formula}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="stack">
        <div className="section-header">
          <p className="eyebrow mono">Grading Tolerances</p>
        </div>
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>Tolerance</th>
                <th>Example</th>
              </tr>
            </thead>
            <tbody>
              {TOLERANCES.map((t) => (
                <tr key={t.metric}>
                  <td>{t.metric}</td>
                  <td className="mono positive">{t.tolerance}</td>
                  <td className="muted small">{t.example}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="stack">
        <div className="section-header">
          <p className="eyebrow mono">Difficulty Levels</p>
        </div>
        <div className="grid-3">
          {DIFFICULTIES.map((d) => (
            <div key={d.id} className="card card-accent-blue">
              <p className="metric-label">{d.id}</p>
              <p className="small">{d.desc}</p>
              <div className="divider"></div>
              <p className="mono small positive">{d.graded}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

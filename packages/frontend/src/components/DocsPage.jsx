const ENDPOINTS = [
  { method: "POST", path: "/reset",                desc: "Initialize episode with task_id" },
  { method: "POST", path: "/step",                 desc: "Execute MCP tool call via CallToolAction" },
  { method: "GET",  path: "/state",                desc: "Current episode state (task_id, is_done)" },
  { method: "GET",  path: "/health",               desc: "Health check" },
  { method: "POST", path: "/api/load-scenario",    desc: "Load seed data into the API store" },
  { method: "GET",  path: "/api/portfolio",        desc: "Fund-level summary (NAV, MOIC, IRR)" },
  { method: "GET",  path: "/api/bridge/{fund_id}", desc: "8-line NAV bridge for a fund" },
  { method: "GET",  path: "/api/deals/{fund_id}",  desc: "Deals + ownership per fund" },
  { method: "GET",  path: "/api/cashflows/{fund_id}", desc: "Cashflow records + totals" },
  { method: "GET",  path: "/api/sectors",          desc: "Sector breakdown across funds" },
  { method: "POST", path: "/api/run-agent",        desc: "Run baseline agent and return all steps + grading" },
];

const MCP_TOOLS = [
  { name: "get_available_filters",  desc: "List fund_ids, deal_ids, sectors" },
  { name: "get_portfolio_summary",  desc: "Fund-level NAV, MOIC, IRR" },
  { name: "get_nav_bridge",         desc: "8-line NAV bridge for one fund" },
  { name: "get_irr",                desc: "IRR for one fund" },
  { name: "compare_funds",          desc: "Side-by-side fund comparison" },
  { name: "get_sector_report",      desc: "Grouped by property sector" },
  { name: "get_deal_exposure",      desc: "Deal across all holding funds" },
  { name: "get_raw_cashflows",      desc: "Paginated cashflow records" },
  { name: "get_cashflow_summary",   desc: "Pre-aggregated totals + IRR schedule" },
  { name: "get_deal_info",          desc: "Property-level ownership, appraiser NAV" },
  { name: "get_portfolio_bridge",   desc: "NAV bridge across all funds" },
  { name: "get_deal_bridge",        desc: "NAV bridge for single deal" },
  { name: "get_deal_metrics",       desc: "MOIC and IRR for single deal" },
  { name: "get_portfolio_metrics",  desc: "Portfolio-wide MOIC and IRR" },
  { name: "submit_report",          desc: "Grade submission, returns reward 0.0-1.0" },
];

const TOLERANCES = [
  { metric: "NAV bridge amounts", tolerance: "± $0.50M",     example: "Correct 100.00 → accept 99.50–100.50" },
  { metric: "MOIC (multiple)",    tolerance: "± 0.02x",      example: "Correct 1.50 → accept 1.48–1.52" },
  { metric: "IRR",                tolerance: "± 1.0% absolute", example: "Correct 0.150 → accept 0.140–0.160" },
];

const DIFFICULTIES = [
  {
    id: "easy",
    name: "Easy",
    desc: "RE Alpha Fund I — 3 properties, 100% owned. Compute the 8-line NAV bridge.",
    graded: "Bridge only · 8 items",
  },
  {
    id: "medium",
    name: "Medium",
    desc: "RE Beta Fund II — 5 properties including a Data Center. Bridge + MOIC.",
    graded: "Bridge 60% · MOIC 40%",
  },
  {
    id: "hard",
    name: "Hard",
    desc: "Cross-fund Alpha + Beta + Gamma. Co-investment in Prestige Tower.",
    graded: "Bridge 50% · MOIC + IRR 50%",
  },
];

const BRIDGE_LINES = [
  ["Beginning NAV",      "Appraiser value at period start"],
  ["+ Contribution",     "Capital deployed during the period"],
  ["− Disposition",      "Sale proceeds during the period"],
  ["+ Income",           "Rental / operating income during the period"],
  ["= Cash-Adjusted NAV","Beginning + Contribution − Disposition + Income"],
  ["− Income Reversal",  "−Income (income removed from valuation)"],
  ["± Write Up/Down",    "Plug = Ending NAV − (Cash-Adjusted + Income Reversal)"],
  ["= Ending NAV",       "Appraiser value at period end"],
];

export default function DocsPage() {
  return (
    <div className="md-stack-lg md-reveal">
      {/* ── Hero ── */}
      <section className="md-surface-hero">
        <div className="md-stack">
          <span className="md-eyebrow">05 — Reference</span>
          <h2 className="md-section-title">Documentation</h2>
          <p className="md-body-large md-on-surface-variant" style={{ maxWidth: 680 }}>
            FundLens is an OpenEnv environment for grading AI agents on
            real-estate private-equity fund reporting. The complete reference
            lives here. Run <code>make docs</code> for the standalone docs site.
          </p>
        </div>
      </section>

      {/* ── HTTP API ── */}
      <section className="md-stack">
        <div className="md-stack-sm">
          <span className="md-eyebrow">HTTP endpoints</span>
          <h3 className="md-headline-small">Reach the environment</h3>
        </div>
        <div className="md-card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="md-table-wrap" style={{ background: "transparent", borderRadius: 0 }}>
            <table className="md-table md-table-reveal">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Path</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {ENDPOINTS.map((e) => (
                  <tr key={e.path + e.method}>
                    <td>
                      <span
                        className={`md-badge ${
                          e.method === "GET" ? "md-badge-primary" : "md-badge-tertiary"
                        }`}
                      >
                        {e.method}
                      </span>
                    </td>
                    <td>
                      <code>{e.path}</code>
                    </td>
                    <td className="md-body-small md-on-surface-variant">{e.desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── MCP Tools ── */}
      <section className="md-stack">
        <div className="md-stack-sm">
          <span className="md-eyebrow">MCP tools</span>
          <h3 className="md-headline-small">{MCP_TOOLS.length} registered tools</h3>
        </div>
        <div className="md-card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="md-table-wrap" style={{ background: "transparent", borderRadius: 0 }}>
            <table className="md-table md-table-reveal">
              <thead>
                <tr>
                  <th>Tool</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {MCP_TOOLS.map((t) => (
                  <tr key={t.name}>
                    <td>
                      <code>{t.name}</code>
                    </td>
                    <td className="md-body-small md-on-surface-variant">{t.desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── NAV Bridge formula ── */}
      <section className="md-stack">
        <div className="md-stack-sm">
          <span className="md-eyebrow">NAV bridge formula</span>
          <h3 className="md-headline-small">Eight lines, every quarter</h3>
        </div>
        <div className="md-card md-card-tonal-secondary">
          <div className="md-stack-sm">
            {BRIDGE_LINES.map(([line, formula]) => (
              <div
                key={line}
                className="md-row-spread"
                style={{
                  paddingBottom: "var(--md-space-2)",
                  borderBottom: "1px solid rgba(0,0,0,0.06)",
                }}
              >
                <code style={{ background: "transparent", padding: 0, color: "var(--md-on-secondary-container)" }}>
                  {line}
                </code>
                <span
                  className="md-body-small"
                  style={{ color: "var(--md-on-secondary-container)", opacity: 0.75 }}
                >
                  {formula}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Grading tolerances ── */}
      <section className="md-stack">
        <div className="md-stack-sm">
          <span className="md-eyebrow">Grading tolerances</span>
          <h3 className="md-headline-small">How submissions are scored</h3>
        </div>
        <div className="md-card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="md-table-wrap" style={{ background: "transparent", borderRadius: 0 }}>
            <table className="md-table md-table-reveal">
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
                    <td className="md-num md-pos">{t.tolerance}</td>
                    <td className="md-body-small md-on-surface-variant">
                      {t.example}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── Difficulty levels ── */}
      <section className="md-stack">
        <div className="md-stack-sm">
          <span className="md-eyebrow">Difficulty levels</span>
          <h3 className="md-headline-small">Three task tiers</h3>
        </div>
        <div className="md-grid md-grid-3">
          {DIFFICULTIES.map((d) => (
            <div key={d.id} className="md-card md-card-interactive">
              <div className="md-stack-sm">
                <span className="md-badge md-badge-primary">{d.name}</span>
                <p className="md-body-medium md-on-surface">{d.desc}</p>
                <div className="md-divider" />
                <span className="md-label-large md-primary-text">{d.graded}</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

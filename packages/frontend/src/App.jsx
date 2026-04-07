import { useState, useCallback } from "react";
import "./index.css";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [taskId, setTaskId] = useState("easy");
  const [scenario, setScenario] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const loadScenario = useCallback(async (id) => {
    setLoading(true);
    setScenario(null);
    setResult(null);
    try {
      await fetch(`/api/load-scenario?task_id=${id}`, { method: "POST" });
      const resp = await fetch("/api/portfolio");
      const data = await resp.json();
      setScenario({ taskId: id, portfolio: data });
    } catch (err) {
      console.error("Load scenario failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const PAGES = [
    { id: "dashboard", label: "Dashboard" },
    { id: "bridge", label: "NAV Bridge" },
    { id: "explorer", label: "Explorer" },
    { id: "agent", label: "Agent" },
    { id: "docs", label: "Docs" },
  ];

  return (
    <div className="app-shell">
      <header className="app-header container">
        <div>
          <h1 className="app-title serif">FundLens</h1>
          <p className="app-subtitle mono">PE Fund NAV Bridge Environment</p>
        </div>
        <div className="row" style={{ gap: "var(--space-2)" }}>
          <span className="badge badge-emerald">v0.2</span>
          <span className="badge badge-blue">OpenEnv</span>
        </div>
      </header>

      <nav className="app-nav container">
        {PAGES.map((p) => (
          <button
            key={p.id}
            type="button"
            className={`tab ${page === p.id ? "active" : ""}`}
            onClick={() => setPage(p.id)}
          >
            {p.label}
          </button>
        ))}
      </nav>

      <main className="app-main container fade-in" key={page}>
        {page === "dashboard" && (
          <div className="stack">
            <div className="stack-sm">
              <span className="section-eyebrow">Section 01 / Portfolio</span>
              <h2 className="section-title">Portfolio Dashboard</h2>
              <p className="muted">
                Load a difficulty scenario to begin exploring the PE fund portfolio
                and its underlying NAV bridges.
              </p>
            </div>

            <div className="row">
              {["easy", "medium", "hard"].map((id) => (
                <button
                  key={id}
                  type="button"
                  className={`tab ${taskId === id ? "active" : ""}`}
                  onClick={() => setTaskId(id)}
                >
                  {id.charAt(0).toUpperCase() + id.slice(1)}
                </button>
              ))}
              <button
                type="button"
                className="btn-primary"
                onClick={() => loadScenario(taskId)}
                disabled={loading}
              >
                {loading ? "Loading..." : "Load Scenario"}
              </button>
            </div>

            {scenario && (
              <div className="stack fade-in">
                <div className="row-spread">
                  <h3 className="serif">
                    Funds Loaded
                    <span className="badge badge-emerald" style={{ marginLeft: "var(--space-3)" }}>
                      {scenario.taskId}
                    </span>
                  </h3>
                  <span className="metric-label">
                    {Object.keys(scenario.portfolio).length} fund
                    {Object.keys(scenario.portfolio).length === 1 ? "" : "s"}
                  </span>
                </div>
                <div className="fund-grid">
                  {Object.entries(scenario.portfolio).map(([fid, fund]) => (
                    <div key={fid} className="card card-accent-emerald">
                      <div>
                        <p className="metric-label">{fid}</p>
                        <h4 className="serif" style={{ marginTop: "var(--space-1)" }}>
                          {fund.fund_name}
                        </h4>
                      </div>
                      <div className="row">
                        <div>
                          <p className="metric-label">Beginning NAV</p>
                          <p className="metric-number">
                            ${fund.beginning_nav}
                            <span className="faint" style={{ fontSize: "0.7em" }}>M</span>
                          </p>
                        </div>
                        <div>
                          <p className="metric-label">Ending NAV</p>
                          <p className="metric-number">
                            ${fund.ending_nav}
                            <span className="faint" style={{ fontSize: "0.7em" }}>M</span>
                          </p>
                        </div>
                      </div>
                      <hr className="divider" />
                      <div className="row">
                        <div>
                          <p className="metric-label">MOIC</p>
                          <p className="metric-number positive">
                            {fund.moic?.toFixed(2)}x
                          </p>
                        </div>
                        <div>
                          <p className="metric-label">IRR</p>
                          <p className="metric-number positive">
                            {((fund.irr || 0) * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {page === "bridge" && (
          <div className="stack">
            <div className="stack-sm">
              <span className="section-eyebrow">Section 02 / Reconciliation</span>
              <h2 className="section-title">NAV Bridge</h2>
              <p className="muted">
                Coming soon -- select a fund to view its 8-line NAV bridge with
                contributions, distributions, realized and unrealized gains.
              </p>
            </div>
          </div>
        )}

        {page === "explorer" && (
          <div className="stack">
            <div className="stack-sm">
              <span className="section-eyebrow">Section 03 / Holdings</span>
              <h2 className="section-title">Fund Explorer</h2>
              <p className="muted">
                Coming soon -- deals, cashflows, and sector breakdowns for each
                portfolio fund.
              </p>
            </div>
          </div>
        )}

        {page === "agent" && (
          <div className="stack">
            <div className="stack-sm">
              <span className="section-eyebrow">Section 04 / Evaluation</span>
              <h2 className="section-title">Agent Runner</h2>
              <p className="muted">
                Coming soon -- run the baseline LLM agent against the environment
                and grade its NAV bridge submissions.
              </p>
            </div>
          </div>
        )}

        {page === "docs" && (
          <div className="stack">
            <div className="stack-sm">
              <span className="section-eyebrow">Section 05 / Reference</span>
              <h2 className="section-title">Documentation</h2>
              <p className="muted">
                Coming soon -- API reference, data models, and grading tolerances
                for the FundLens environment.
              </p>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer container">
        <span className="mono muted">FundLens v0.2</span>
        <span className="mono muted">Scaler x Meta PyTorch Hackathon 2026</span>
      </footer>
    </div>
  );
}

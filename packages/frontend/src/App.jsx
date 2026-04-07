import { useCallback, useState } from "react";
import Dashboard from "./components/Dashboard.jsx";
import NAVBridge from "./components/NAVBridge.jsx";
import FundExplorer from "./components/FundExplorer.jsx";
import AgentRunner from "./components/AgentRunner.jsx";
import DocsPage from "./components/DocsPage.jsx";
import "./index.css";

const PAGES = [
  { id: "dashboard", label: "Dashboard" },
  { id: "bridge", label: "NAV Bridge" },
  { id: "explorer", label: "Explorer" },
  { id: "agent", label: "Agent" },
  { id: "docs", label: "Docs" },
];

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [taskId, setTaskId] = useState("easy");
  const [scenario, setScenario] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);

  const loadScenario = useCallback(async (id) => {
    setLoading(true);
    setLoadError(null);
    setScenario(null);
    try {
      const loadResp = await fetch(`/api/load-scenario?task_id=${id}`, {
        method: "POST",
      });
      if (!loadResp.ok) throw new Error(`load-scenario ${loadResp.status}`);
      const portfolioResp = await fetch("/api/portfolio");
      if (!portfolioResp.ok) throw new Error(`portfolio ${portfolioResp.status}`);
      const data = await portfolioResp.json();
      setScenario({ taskId: id, portfolio: data });
    } catch (err) {
      console.error("Load scenario failed:", err);
      setLoadError(err.message || "Failed to load scenario");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="app-shell">
      <div className="md-container">
        <header className="app-header">
          <div className="app-brand">
            <div className="app-brand-mark">
              <span className="app-logo-dot" aria-hidden="true">F</span>
              <h1 className="app-title">FundLens</h1>
            </div>
            <p className="app-subtitle">
              PE Fund NAV Bridge Environment · OpenEnv compliant
            </p>
          </div>
        </header>

        <div className="app-nav-row">
          <nav className="md-tabs" role="tablist" aria-label="Pages">
            {PAGES.map((p) => (
              <button
                key={p.id}
                type="button"
                role="tab"
                aria-selected={page === p.id}
                className={`md-tab ${page === p.id ? "is-active" : ""}`}
                onClick={() => setPage(p.id)}
              >
                {p.label}
              </button>
            ))}
          </nav>
        </div>

        <main className="app-main md-fade-in" key={page}>
          {page === "dashboard" && (
            <Dashboard
              taskId={taskId}
              setTaskId={setTaskId}
              scenario={scenario}
              loading={loading}
              loadError={loadError}
              onLoadScenario={loadScenario}
            />
          )}

          {page === "bridge" && <NAVBridge scenario={scenario} />}

          {page === "explorer" && <FundExplorer scenario={scenario} />}

          {page === "agent" && (
            <AgentRunner taskId={taskId} setTaskId={setTaskId} />
          )}

          {page === "docs" && <DocsPage />}
        </main>

        <footer className="app-footer">
          <span>FundLens v0.2 · {new Date().getFullYear()}</span>
          <span>Scaler × Meta PyTorch Hackathon</span>
        </footer>
      </div>
    </div>
  );
}

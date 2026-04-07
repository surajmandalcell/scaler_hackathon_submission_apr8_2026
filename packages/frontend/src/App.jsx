import { useCallback, useState } from "react";
import AnalystView from "./components/AnalystView.jsx";
import AdminView from "./components/AdminView.jsx";
import InvestorView from "./components/InvestorView.jsx";
import Playground from "./components/Playground.jsx";
import DocsPage from "./components/DocsPage.jsx";
import "./index.css";

// Top-level "persona" switcher. Each view owns its own sub-nav; see the
// individual *View components for sub-tab layouts.
const VIEWS = [
  { id: "analyst",    label: "Analyst" },
  { id: "admin",      label: "Admin" },
  { id: "investor",   label: "Investor" },
  { id: "playground", label: "Playground" },
  { id: "docs",       label: "Docs" },
];

export default function App() {
  const [view, setView] = useState("analyst");
  const [taskId, setTaskId] = useState("easy");
  const [scenario, setScenario] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);

  const refreshPortfolio = useCallback(async () => {
    try {
      const portfolioResp = await fetch("/api/portfolio");
      if (!portfolioResp.ok) throw new Error(`portfolio ${portfolioResp.status}`);
      const data = await portfolioResp.json();
      setScenario((prev) => ({
        taskId: prev?.taskId ?? taskId,
        portfolio: data,
      }));
    } catch (err) {
      console.error("Refresh portfolio failed:", err);
    }
  }, [taskId]);

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

  // Re-fetch the portfolio whenever the Admin tab mutates the store, so the
  // Analyst/Investor views don't show stale data.
  const onStoreMutated = useCallback(() => {
    refreshPortfolio();
  }, [refreshPortfolio]);

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
          <nav className="md-tabs" role="tablist" aria-label="Views">
            {VIEWS.map((v) => (
              <button
                key={v.id}
                type="button"
                role="tab"
                aria-selected={view === v.id}
                className={`md-tab ${view === v.id ? "is-active" : ""}`}
                onClick={() => setView(v.id)}
              >
                {v.label}
              </button>
            ))}
          </nav>
        </div>

        <main className="app-main md-fade-in" key={view}>
          {view === "analyst" && (
            <AnalystView
              taskId={taskId}
              setTaskId={setTaskId}
              scenario={scenario}
              loading={loading}
              loadError={loadError}
              onLoadScenario={loadScenario}
            />
          )}

          {view === "admin" && (
            <AdminView
              taskId={taskId}
              setTaskId={setTaskId}
              scenario={scenario}
              onStoreMutated={onStoreMutated}
            />
          )}

          {view === "investor" && (
            <InvestorView scenario={scenario} taskId={taskId} />
          )}

          {view === "playground" && <Playground />}

          {view === "docs" && <DocsPage />}
        </main>

        <footer className="app-footer">
          <span>FundLens v0.3 · {new Date().getFullYear()}</span>
          <span>Scaler × Meta PyTorch Hackathon</span>
        </footer>
      </div>
    </div>
  );
}

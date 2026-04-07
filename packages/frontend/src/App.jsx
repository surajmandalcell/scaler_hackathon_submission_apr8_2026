import { useState, useCallback } from "react";
import Dashboard from "./components/Dashboard.jsx";
import ScoreCard from "./components/ScoreCard.jsx";
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

  return (
    <div className="app-shell">
      <header className="app-header container">
        <div>
          <h1 className="app-title serif">FundLens</h1>
          <p className="app-subtitle mono">PE Fund NAV Bridge Environment</p>
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

      <main className="app-main container fade-in">
        {page === "dashboard" && (
          <>
            <Dashboard
              taskId={taskId}
              setTaskId={setTaskId}
              scenario={scenario}
              loading={loading}
              onLoadScenario={loadScenario}
            />
            <ScoreCard result={result} />
          </>
        )}

        {page === "bridge" && (
          <div className="stack">
            <h2 className="serif section-title">NAV Bridge</h2>
            <p className="muted">Coming soon - select a fund to view its 8-line NAV bridge.</p>
          </div>
        )}

        {page === "explorer" && (
          <div className="stack">
            <h2 className="serif section-title">Fund Explorer</h2>
            <p className="muted">Coming soon - deals, cashflows, and sector breakdowns.</p>
          </div>
        )}

        {page === "agent" && (
          <div className="stack">
            <h2 className="serif section-title">Agent Runner</h2>
            <p className="muted">Coming soon - run the baseline LLM agent against the environment.</p>
          </div>
        )}

        {page === "docs" && (
          <div className="stack">
            <h2 className="serif section-title">Documentation</h2>
            <p className="muted">Coming soon - API reference, data models, grading tolerances.</p>
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

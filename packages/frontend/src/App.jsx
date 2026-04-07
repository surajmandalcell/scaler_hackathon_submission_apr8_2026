import { useState, useCallback } from "react";
import Dashboard from "./components/Dashboard.jsx";
import ScoreCard from "./components/ScoreCard.jsx";
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

        {page === "bridge" && <NAVBridge scenario={scenario} />}

        {page === "explorer" && <FundExplorer scenario={scenario} />}

        {page === "agent" && (
          <AgentRunner taskId={taskId} scenario={scenario} onResult={setResult} />
        )}

        {page === "docs" && <DocsPage />}
      </main>

      <footer className="app-footer container">
        <span className="mono muted">FundLens v0.2</span>
        <span className="mono muted">Scaler x Meta PyTorch Hackathon 2026</span>
      </footer>
    </div>
  );
}

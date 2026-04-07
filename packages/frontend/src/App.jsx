import { useCallback, useState } from "react";
import NavRail from "./components/NavRail.jsx";
import AnalystView from "./components/AnalystView.jsx";
import AdminView from "./components/AdminView.jsx";
import InvestorView from "./components/InvestorView.jsx";
import Playground from "./components/Playground.jsx";
import DocsPage from "./components/DocsPage.jsx";
import "./index.css";

// Top-level personas surfaced in the navigation rail. Each owns its own
// internal sub-tab nav, so the app shell only ever has ONE horizontal tab
// row visible at a time -- this is the MD3 navigation-rail pattern, not the
// previous double-stacked-tabs layout.
const VIEWS = [
  { id: "analyst",    label: "Analyst" },
  { id: "admin",      label: "Admin" },
  { id: "investor",   label: "Investor" },
  { id: "playground", label: "Playground" },
  { id: "docs",       label: "Docs" },
];

const VIEW_HEADERS = {
  analyst:    { eyebrow: "Persona", title: "Analyst",    sub: "Explore the scenario data the agent reasons over." },
  admin:      { eyebrow: "Persona", title: "Admin",      sub: "Enter, upload, and reconcile fund data." },
  investor:   { eyebrow: "Persona", title: "Investor",   sub: "Read-only LP portal in plain English." },
  playground: { eyebrow: "Persona", title: "Playground", sub: "Drive the MCP tool surface like an agent does." },
  docs:       { eyebrow: "Persona", title: "Docs",       sub: "Reference for tools, formulas, and grading." },
};

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

  const onStoreMutated = useCallback(() => {
    refreshPortfolio();
  }, [refreshPortfolio]);

  const header = VIEW_HEADERS[view];

  return (
    <div className="app-shell">
      <NavRail items={VIEWS} current={view} onChange={setView} />

      <div className="app-body">
        <div className="app-body-inner">
          <header className="app-header">
            <div className="app-brand">
              <p className="md-eyebrow">{header.eyebrow}</p>
              <h1 className="app-title">{header.title}</h1>
              <p className="app-subtitle">{header.sub}</p>
            </div>
          </header>

          <main className="app-main md-axis-x" key={view}>
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
    </div>
  );
}

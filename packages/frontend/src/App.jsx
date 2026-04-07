import { useCallback, useEffect, useRef, useState } from "react";
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

// How long the outgoing layer is kept mounted, in ms.
// Must be >= the longest md-axis-x-out duration in index.css.
const TRANSITION_HOLD_MS = 420;

function renderView(view, ctx) {
  const { taskId, setTaskId, scenario, loading, loadError, loadScenario, onStoreMutated } = ctx;
  switch (view) {
    case "analyst":
      return (
        <AnalystView
          taskId={taskId}
          setTaskId={setTaskId}
          scenario={scenario}
          loading={loading}
          loadError={loadError}
          onLoadScenario={loadScenario}
        />
      );
    case "admin":
      return (
        <AdminView
          taskId={taskId}
          setTaskId={setTaskId}
          scenario={scenario}
          onStoreMutated={onStoreMutated}
        />
      );
    case "investor":
      return <InvestorView scenario={scenario} taskId={taskId} />;
    case "playground":
      return <Playground />;
    case "docs":
      return <DocsPage />;
    default:
      return null;
  }
}

export default function App() {
  const [view, setView] = useState("analyst");
  const [taskId, setTaskId] = useState("easy");
  const [scenario, setScenario] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);

  // Shared-axis transition state. We keep the previous view mounted for
  // TRANSITION_HOLD_MS so it can animate OUT while the new view animates IN.
  // `transitionKey` increments on every change so React forces a real
  // remount even if `view` cycles back to a prior value -- without this,
  // CSS keyframes only fire on element insertion and the user perceives a
  // hard cut.
  const [previousView, setPreviousView] = useState(null);
  const [transitionKey, setTransitionKey] = useState(0);
  const holdTimer = useRef(null);

  const handleSetView = useCallback((next) => {
    setView((current) => {
      if (current === next) return current;
      setPreviousView(current);
      setTransitionKey((k) => k + 1);
      if (holdTimer.current) clearTimeout(holdTimer.current);
      holdTimer.current = setTimeout(() => {
        setPreviousView(null);
        holdTimer.current = null;
      }, TRANSITION_HOLD_MS);
      return next;
    });
  }, []);

  useEffect(() => () => {
    if (holdTimer.current) clearTimeout(holdTimer.current);
  }, []);

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
  const ctx = { taskId, setTaskId, scenario, loading, loadError, loadScenario, onStoreMutated };

  return (
    <div className="app-shell">
      <NavRail items={VIEWS} current={view} onChange={handleSetView} />

      <div className="app-body">
        <div className="app-body-inner">
          <header
            className="app-header md-axis-y-soft"
            // Re-key the header on view change so the title fades+slides
            // alongside the main content.
            key={`header-${transitionKey}`}
          >
            <div className="app-brand">
              <p className="md-eyebrow">{header.eyebrow}</p>
              <h1 className="app-title">{header.title}</h1>
              <p className="app-subtitle">{header.sub}</p>
            </div>
          </header>

          <main className="app-main">
            <div className="md-axis-stage" data-testid="view-stage">
              {previousView && previousView !== view && (
                <div
                  key={`out-${transitionKey}`}
                  className="md-axis-layer md-axis-layer--out md-axis-x"
                  aria-hidden="true"
                >
                  {renderView(previousView, ctx)}
                </div>
              )}
              <div
                key={`in-${transitionKey}-${view}`}
                className="md-axis-layer md-axis-layer--in md-axis-x"
                data-testid="view-layer-in"
              >
                {renderView(view, ctx)}
              </div>
            </div>
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

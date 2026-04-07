import { useCallback, useEffect, useRef, useState } from "react";
import Dashboard from "./Dashboard.jsx";
import NAVBridge from "./NAVBridge.jsx";
import FundExplorer from "./FundExplorer.jsx";
import AgentRunner from "./AgentRunner.jsx";

const ANALYST_TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "bridge",    label: "NAV Bridge" },
  { id: "explorer",  label: "Explorer" },
  { id: "agent",     label: "Agent" },
];

const TRANSITION_HOLD_MS = 320;

function renderTab(tab, ctx) {
  const { taskId, setTaskId, scenario, loading, loadError, onLoadScenario } = ctx;
  switch (tab) {
    case "dashboard":
      return (
        <Dashboard
          taskId={taskId}
          setTaskId={setTaskId}
          scenario={scenario}
          loading={loading}
          loadError={loadError}
          onLoadScenario={onLoadScenario}
        />
      );
    case "bridge":
      return <NAVBridge scenario={scenario} />;
    case "explorer":
      return <FundExplorer scenario={scenario} />;
    case "agent":
      return <AgentRunner taskId={taskId} setTaskId={setTaskId} />;
    default:
      return null;
  }
}

export default function AnalystView(props) {
  const [tab, setTab] = useState("dashboard");
  // Same shared-axis pattern App.jsx uses for top-level views, but on the
  // Y axis. The OUTGOING tab is held mounted for TRANSITION_HOLD_MS so it
  // can animate out while the new tab animates in -- without this React
  // would reuse the DOM node and the keyframes would never replay.
  const [previousTab, setPreviousTab] = useState(null);
  const [transitionKey, setTransitionKey] = useState(0);
  const holdTimer = useRef(null);

  const handleSetTab = useCallback((next) => {
    setTab((current) => {
      if (current === next) return current;
      setPreviousTab(current);
      setTransitionKey((k) => k + 1);
      if (holdTimer.current) clearTimeout(holdTimer.current);
      holdTimer.current = setTimeout(() => {
        setPreviousTab(null);
        holdTimer.current = null;
      }, TRANSITION_HOLD_MS);
      return next;
    });
  }, []);

  useEffect(() => () => {
    if (holdTimer.current) clearTimeout(holdTimer.current);
  }, []);

  return (
    <>
      <nav className="md-tabs md-tabs-sub" role="tablist" aria-label="Analyst sub-tabs">
        {ANALYST_TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`md-tab md-tab-sub ${tab === t.id ? "is-active" : ""}`}
            onClick={() => handleSetTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="md-axis-stage">
        {previousTab && previousTab !== tab && (
          <div
            key={`out-${transitionKey}`}
            className="md-axis-layer md-axis-layer--out md-axis-y"
            aria-hidden="true"
          >
            {renderTab(previousTab, props)}
          </div>
        )}
        <div
          key={`in-${transitionKey}-${tab}`}
          className="md-axis-layer md-axis-layer--in md-axis-y"
        >
          {renderTab(tab, props)}
        </div>
      </div>
    </>
  );
}

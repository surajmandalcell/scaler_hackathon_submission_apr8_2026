import { useState } from "react";
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

export default function AnalystView({
  taskId,
  setTaskId,
  scenario,
  loading,
  loadError,
  onLoadScenario,
}) {
  const [tab, setTab] = useState("dashboard");

  return (
    <div className="md-stack-lg">
      <nav className="md-tabs md-tabs-sub" role="tablist" aria-label="Analyst sub-tabs">
        {ANALYST_TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className={`md-tab md-tab-sub ${tab === t.id ? "is-active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="md-fade-in" key={tab}>
        {tab === "dashboard" && (
          <Dashboard
            taskId={taskId}
            setTaskId={setTaskId}
            scenario={scenario}
            loading={loading}
            loadError={loadError}
            onLoadScenario={onLoadScenario}
          />
        )}
        {tab === "bridge" && <NAVBridge scenario={scenario} />}
        {tab === "explorer" && <FundExplorer scenario={scenario} />}
        {tab === "agent" && <AgentRunner taskId={taskId} setTaskId={setTaskId} />}
      </div>
    </div>
  );
}

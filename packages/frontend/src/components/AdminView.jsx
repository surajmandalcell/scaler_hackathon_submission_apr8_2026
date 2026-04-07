import { useCallback, useEffect, useRef, useState } from "react";
import DataEntry from "./admin/DataEntry.jsx";
import Upload from "./admin/Upload.jsx";
import TestRun from "./admin/TestRun.jsx";
import AnswerKey from "./admin/AnswerKey.jsx";

const ADMIN_TABS = [
  { id: "data",   label: "Data Entry" },
  { id: "upload", label: "Upload" },
  { id: "test",   label: "Test Run" },
  { id: "answer", label: "Answer Key" },
];

const TRANSITION_HOLD_MS = 320;

function renderTab(tab, ctx) {
  const { taskId, setTaskId, scenario, onStoreMutated } = ctx;
  switch (tab) {
    case "data":
      return <DataEntry onStoreMutated={onStoreMutated} scenario={scenario} />;
    case "upload":
      return <Upload onStoreMutated={onStoreMutated} />;
    case "test":
      return <TestRun taskId={taskId} setTaskId={setTaskId} />;
    case "answer":
      return <AnswerKey taskId={taskId} setTaskId={setTaskId} />;
    default:
      return null;
  }
}

export default function AdminView(props) {
  const [tab, setTab] = useState("data");
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
      <nav className="md-tabs md-tabs-sub" role="tablist" aria-label="Admin sub-tabs">
        {ADMIN_TABS.map((t) => (
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

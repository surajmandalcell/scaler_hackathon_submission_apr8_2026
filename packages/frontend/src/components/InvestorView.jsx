import { useCallback, useEffect, useRef, useState } from "react";
import Portfolio from "./investor/Portfolio.jsx";
import NAVWalk from "./investor/NAVWalk.jsx";
import ITDSummary from "./investor/ITDSummary.jsx";
import Properties from "./investor/Properties.jsx";

const INVESTOR_TABS = [
  { id: "portfolio",  label: "Portfolio" },
  { id: "navwalk",    label: "NAV Walk" },
  { id: "itd",        label: "ITD Summary" },
  { id: "properties", label: "Properties" },
];

const TRANSITION_HOLD_MS = 320;

function renderTab(tab, ctx) {
  const { scenario, taskId } = ctx;
  switch (tab) {
    case "portfolio":
      return <Portfolio scenario={scenario} taskId={taskId} />;
    case "navwalk":
      return <NAVWalk scenario={scenario} />;
    case "itd":
      return <ITDSummary scenario={scenario} />;
    case "properties":
      return <Properties scenario={scenario} />;
    default:
      return null;
  }
}

export default function InvestorView(props) {
  const [tab, setTab] = useState("portfolio");
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
      <nav className="md-tabs md-tabs-sub" role="tablist" aria-label="Investor sub-tabs">
        {INVESTOR_TABS.map((t) => (
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

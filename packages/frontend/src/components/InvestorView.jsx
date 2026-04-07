import { useState } from "react";
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

export default function InvestorView({ scenario, taskId }) {
  const [tab, setTab] = useState("portfolio");

  return (
    <div className="md-stack-lg">
      <nav className="md-tabs md-tabs-sub" role="tablist" aria-label="Investor sub-tabs">
        {INVESTOR_TABS.map((t) => (
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

      <div className="md-axis-y" key={tab}>
        {tab === "portfolio"  && <Portfolio scenario={scenario} taskId={taskId} />}
        {tab === "navwalk"    && <NAVWalk scenario={scenario} />}
        {tab === "itd"        && <ITDSummary scenario={scenario} />}
        {tab === "properties" && <Properties scenario={scenario} />}
      </div>
    </div>
  );
}

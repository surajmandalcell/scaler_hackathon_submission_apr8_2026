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
      <section className="md-stack-sm">
        <span className="md-eyebrow">LP View</span>
        <h2 className="md-section-title">Investor Portal</h2>
        <p className="md-body-large md-on-surface-variant" style={{ maxWidth: 680 }}>
          The same underlying data as the Analyst view, reframed for a
          non-technical limited partner: plain-English metric labels, no
          jargon, no tool surface. Reflects whatever scenario you've loaded.
        </p>
      </section>

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

      <div className="md-fade-in" key={tab}>
        {tab === "portfolio"  && <Portfolio scenario={scenario} taskId={taskId} />}
        {tab === "navwalk"    && <NAVWalk scenario={scenario} />}
        {tab === "itd"        && <ITDSummary scenario={scenario} />}
        {tab === "properties" && <Properties scenario={scenario} />}
      </div>
    </div>
  );
}

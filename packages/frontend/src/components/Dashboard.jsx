const MODE_LABELS = {
  easy: "NAV Bridge only -- 8 line items",
  medium: "NAV Bridge + MOIC",
  hard: "NAV Bridge + MOIC + IRR (cross-fund)",
};

const DIFFICULTIES = [
  { id: "easy", label: "Easy" },
  { id: "medium", label: "Medium" },
  { id: "hard", label: "Hard" },
];

function formatMovement(beg, end) {
  if (!beg) return `$${end?.toFixed(1)}M`;
  const pct = ((end - beg) / beg) * 100;
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

function isPositive(val) {
  return typeof val === "number" && val >= 0;
}

export default function Dashboard({ taskId, setTaskId, scenario, loading, onLoadScenario }) {
  const showMoic = taskId === "medium" || taskId === "hard";
  const showIrr = taskId === "hard";

  return (
    <div className="stack">
      <div className="section-header">
        <p className="eyebrow mono">01 -- Portfolio</p>
        <h2 className="serif section-title">Dashboard</h2>
      </div>

      <div className="card card-accent-blue">
        <p className="metric-label">Graded at this difficulty</p>
        <p className="mode-description">{MODE_LABELS[taskId]}</p>
      </div>

      <div className="row controls-row">
        <div className="tab-group">
          {DIFFICULTIES.map((d) => (
            <button
              key={d.id}
              type="button"
              className={`tab ${taskId === d.id ? "active" : ""}`}
              onClick={() => setTaskId(d.id)}
            >
              {d.label}
            </button>
          ))}
        </div>
        <button
          type="button"
          className="btn-primary"
          onClick={() => onLoadScenario(taskId)}
          disabled={loading}
        >
          {loading ? "Loading..." : "Load Scenario"}
        </button>
      </div>

      {!scenario && !loading && (
        <div className="empty-state">
          <p className="serif muted">Choose a difficulty and load a scenario to begin.</p>
        </div>
      )}

      {scenario && (
        <div className="stack">
          <div className="section-header">
            <p className="eyebrow mono">Funds loaded -- {scenario.taskId}</p>
          </div>
          <div className="fund-grid">
            {Object.entries(scenario.portfolio).map(([fid, fund]) => {
              const movement = fund.ending_nav - fund.beginning_nav;
              return (
                <div key={fid} className="card card-accent-emerald fade-in">
                  <p className="metric-label">{fid}</p>
                  <h3 className="serif fund-name">{fund.fund_name}</h3>
                  <div className="divider"></div>
                  <div className="row metric-row">
                    <div>
                      <p className="metric-label">Beginning</p>
                      <p className="metric-number">${fund.beginning_nav}M</p>
                    </div>
                    <div className="arrow mono">-&gt;</div>
                    <div>
                      <p className="metric-label">Ending</p>
                      <p className="metric-number">${fund.ending_nav}M</p>
                    </div>
                  </div>
                  <p className={`movement mono ${isPositive(movement) ? "positive" : "negative"}`}>
                    {formatMovement(fund.beginning_nav, fund.ending_nav)}
                  </p>
                  <div className="divider"></div>
                  <div className="row metric-row">
                    {showMoic && (
                      <div>
                        <p className="metric-label">MOIC</p>
                        <p className="metric-number positive">{fund.moic?.toFixed(2)}x</p>
                      </div>
                    )}
                    {showIrr && (
                      <div>
                        <p className="metric-label">IRR</p>
                        <p className="metric-number positive">
                          {((fund.irr || 0) * 100).toFixed(1)}%
                        </p>
                      </div>
                    )}
                    {!showMoic && !showIrr && (
                      <p className="muted small">Metrics not graded at easy difficulty.</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

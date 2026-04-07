const DIFFICULTIES = [
  { id: "easy",   label: "Easy" },
  { id: "medium", label: "Medium" },
  { id: "hard",   label: "Hard" },
];

const MODE_LABELS = {
  easy:   "NAV Bridge — 8 line items",
  medium: "NAV Bridge + MOIC",
  hard:   "NAV Bridge + MOIC + IRR (cross-fund)",
};

const MODE_DESCRIPTIONS = {
  easy:   "RE Alpha Fund I — 3 properties, all 100% owned. Compute the 8-line NAV bridge.",
  medium: "RE Beta Fund II — 5 properties, 100% owned. Compute the bridge plus MOIC.",
  hard:   "Alpha + Beta + Gamma cross-fund. Compute bridge + MOIC + IRR with co-investment.",
};

function formatCurrency(value) {
  if (value === undefined || value === null) return "—";
  return `$${Number(value).toFixed(1)}M`;
}

function formatMovement(beg, end) {
  if (!beg) return "—";
  const pct = ((end - beg) / beg) * 100;
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

function isPositive(val) {
  return typeof val === "number" && val >= 0;
}

export default function Dashboard({
  taskId,
  setTaskId,
  scenario,
  loading,
  loadError,
  onLoadScenario,
}) {
  const showMoic = taskId === "medium" || taskId === "hard";
  const showIrr  = taskId === "hard";

  return (
    <div className="md-stack-lg md-reveal">
      {/* ── Hero ── */}
      <section className="md-surface-hero">
        <div className="md-stack">
          <span className="md-eyebrow">01 — Portfolio</span>
          <h2 className="md-section-title">Choose a difficulty</h2>
          <p className="md-body-large md-on-surface-variant" style={{ maxWidth: 640 }}>
            FundLens grades AI agents on private-equity fund reporting.
            Pick a difficulty, load the scenario, and explore the data the
            agent will reason over.
          </p>

          <div className="md-row" role="group" aria-label="Difficulty">
            {DIFFICULTIES.map((d) => (
              <button
                key={d.id}
                type="button"
                className={`md-chip ${taskId === d.id ? "is-selected" : ""}`}
                onClick={() => setTaskId(d.id)}
                aria-pressed={taskId === d.id}
              >
                {d.label}
              </button>
            ))}
          </div>

          <div className="md-stack-sm">
            <p className="md-label-large md-on-surface-variant">
              Graded at this level
            </p>
            <p className="md-title-large md-on-surface">{MODE_LABELS[taskId]}</p>
            <p className="md-body-medium md-on-surface-variant">
              {MODE_DESCRIPTIONS[taskId]}
            </p>
          </div>

          <div className="md-row">
            <button
              type="button"
              className="md-btn md-btn-filled md-btn-lg"
              onClick={() => onLoadScenario(taskId)}
              disabled={loading}
            >
              {loading ? "Loading…" : "Load scenario"}
            </button>
            {scenario && (
              <span className="md-badge md-badge-success">
                {scenario.taskId} loaded
              </span>
            )}
          </div>

          {loadError && (
            <p className="md-body-medium md-error-text">
              Could not load: {loadError}
            </p>
          )}
        </div>
      </section>

      {/* ── Funds grid ── */}
      {scenario && (
        <section className="md-stack">
          <div className="md-stack-sm">
            <span className="md-eyebrow">Funds in play</span>
            <h3 className="md-headline-medium md-on-surface">
              {Object.keys(scenario.portfolio).length}{" "}
              {Object.keys(scenario.portfolio).length === 1 ? "fund" : "funds"} loaded
            </h3>
          </div>

          <div className="md-grid md-grid-auto md-stagger">
            {Object.entries(scenario.portfolio).map(([fid, fund]) => {
              const movement = fund.ending_nav - fund.beginning_nav;
              const positive = isPositive(movement);
              return (
                <article
                  key={fid}
                  className="md-card md-card-interactive"
                  aria-label={fund.fund_name}
                >
                  <div className="md-stack">
                    <div className="md-row-spread">
                      <span className="md-badge md-badge-primary">{fid}</span>
                      <span
                        className={`md-label-large ${positive ? "md-pos" : "md-neg"}`}
                      >
                        {formatMovement(fund.beginning_nav, fund.ending_nav)}
                      </span>
                    </div>

                    <h4 className="md-title-large">{fund.fund_name}</h4>

                    <div className="md-row" style={{ gap: "var(--md-space-7)" }}>
                      <div className="md-metric">
                        <span className="md-metric-label">Beginning</span>
                        <span className="md-metric-value">
                          {formatCurrency(fund.beginning_nav)}
                        </span>
                      </div>
                      <div className="md-metric">
                        <span className="md-metric-label">Ending</span>
                        <span className="md-metric-value">
                          {formatCurrency(fund.ending_nav)}
                        </span>
                      </div>
                    </div>

                    {(showMoic || showIrr) && (
                      <>
                        <div className="md-divider" />
                        <div className="md-row" style={{ gap: "var(--md-space-7)" }}>
                          {showMoic && (
                            <div className="md-metric">
                              <span className="md-metric-label">MOIC</span>
                              <span className="md-metric-value md-pos">
                                {fund.moic?.toFixed(2)}x
                              </span>
                            </div>
                          )}
                          {showIrr && (
                            <div className="md-metric">
                              <span className="md-metric-label">IRR</span>
                              <span className="md-metric-value md-pos">
                                {((fund.irr || 0) * 100).toFixed(1)}%
                              </span>
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )}

      {!scenario && !loading && !loadError && (
        <div className="md-empty">
          <span className="md-empty-title">No scenario loaded</span>
          <span className="md-empty-text">
            Pick a difficulty above and tap “Load scenario” to populate the
            dashboard with realistic fund data.
          </span>
        </div>
      )}
    </div>
  );
}

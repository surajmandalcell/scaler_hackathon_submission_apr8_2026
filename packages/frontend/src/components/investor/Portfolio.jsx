import { MODE_META, irrLabel, moicLabel, navChangeLabel } from "./labels.js";

export default function Portfolio({ scenario, taskId }) {
  const portfolio = scenario?.portfolio;

  if (!portfolio) {
    return (
      <div className="md-empty">
        <p className="md-empty-title">No scenario loaded</p>
        <p className="md-empty-text">
          Switch to the Analyst view and load a scenario, or use the Admin tab
          to enter your own data.
        </p>
      </div>
    );
  }

  const modeInfo = MODE_META[taskId] || {};
  const funds = Object.entries(portfolio);

  return (
    <div className="md-stack-lg">
      {/* Mode banner */}
      <div className="md-card md-card-tonal-primary">
        <div className="md-row" style={{ alignItems: "center" }}>
          <span className="md-badge md-badge-primary">
            {(modeInfo.label || taskId || "No mode").toUpperCase()}
          </span>
          <span className="md-body-medium md-on-surface-variant">
            {modeInfo.graded || "Load a scenario from the Analyst or Admin tab."}
          </span>
        </div>
      </div>

      {/* Metric explainer cards */}
      <div className="md-grid md-grid-auto">
        <div className="md-card md-card-tonal-secondary">
          <div className="md-stack-sm">
            <div className="md-row">
              <span className="md-label-large">MOIC</span>
              <span className="md-badge md-badge-tertiary">Medium & Hard</span>
            </div>
            <p className="md-body-medium md-on-surface-variant">
              <strong className="md-on-surface">Multiple on Invested Capital.</strong>{" "}
              For every $1 you put in, how many $ are you getting back? 2.0x = doubled your money.
            </p>
          </div>
        </div>

        <div className="md-card md-card-tonal-secondary">
          <div className="md-stack-sm">
            <div className="md-row">
              <span className="md-label-large">IRR</span>
              <span className="md-badge md-badge-tertiary">Hard only</span>
            </div>
            <p className="md-body-medium md-on-surface-variant">
              <strong className="md-on-surface">Internal Rate of Return.</strong>{" "}
              The annual growth rate of the investment, accounting for the
              timing of each cashflow. 20%+ is excellent for real estate PE.
            </p>
          </div>
        </div>

        <div className="md-card md-card-tonal-secondary">
          <div className="md-stack-sm">
            <div className="md-row">
              <span className="md-label-large">NAV Walk</span>
              <span className="md-badge md-badge-primary">All modes</span>
            </div>
            <p className="md-body-medium md-on-surface-variant">
              <strong className="md-on-surface">Net Asset Value Bridge.</strong>{" "}
              Step-by-step explanation of how the fund value moved this period.
            </p>
          </div>
        </div>
      </div>

      {/* Fund performance table */}
      <div className="md-stack-sm">
        <span className="md-eyebrow">All funds</span>
        <h3 className="md-headline-small">Performance at a glance</h3>
      </div>

      <div className="md-table-wrap">
        <table className="md-table">
          <thead>
            <tr>
              <th>Fund</th>
              <th>NAV movement (this period)</th>
              <th>MOIC</th>
              <th>IRR</th>
            </tr>
          </thead>
          <tbody>
            {funds.map(([fid, f]) => (
              <tr key={fid}>
                <td><strong>{f.fund_name}</strong></td>
                <td className="md-mono">{navChangeLabel(f.beginning_nav, f.ending_nav)}</td>
                <td className="md-mono">{moicLabel(f.moic, taskId)}</td>
                <td className="md-mono">{irrLabel(f.irr, taskId)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

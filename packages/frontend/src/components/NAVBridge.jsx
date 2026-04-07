import { useState, useEffect } from "react";

const BRIDGE_META = {
  beginning_nav: {
    label: "Opening Value",
    explain: "Where the fund started this period",
    accent: "blue",
    isSubtotal: true,
  },
  contribution: {
    label: "(+) Capital Called",
    explain: "New capital deployed into properties",
    accent: "emerald",
    isSubtotal: false,
  },
  disposition: {
    label: "(-) Sales Proceeds",
    explain: "Cash received from property sales",
    accent: "red",
    isSubtotal: false,
  },
  income: {
    label: "(+) Income Received",
    explain: "Rental and operating income collected",
    accent: "emerald",
    isSubtotal: false,
  },
  cashflow_adjusted_nav: {
    label: "= Cash-Adjusted Value",
    explain: "NAV after all cash movements",
    accent: "blue",
    isSubtotal: true,
  },
  income_reversal: {
    label: "(-) Income Reversal",
    explain: "Income removed from valuation (not a loss)",
    accent: "red",
    isSubtotal: false,
  },
  write_up_down: {
    label: "(+/-) Value Change",
    explain: "Net property valuation change (the plug)",
    accent: "emerald",
    isSubtotal: false,
  },
  ending_nav: {
    label: "= Closing Value",
    explain: "Fund value at end of period",
    accent: "blue",
    isSubtotal: true,
  },
};

const BRIDGE_ORDER = [
  "beginning_nav",
  "contribution",
  "disposition",
  "income",
  "cashflow_adjusted_nav",
  "income_reversal",
  "write_up_down",
  "ending_nav",
];

function formatAmount(n) {
  if (n === undefined || n === null) return "-";
  const sign = n < 0 ? "-" : "";
  return `${sign}$${Math.abs(n).toFixed(2)}M`;
}

export default function NAVBridge({ scenario }) {
  const [selectedFundId, setSelectedFundId] = useState(null);
  const [bridge, setBridge] = useState(null);
  const [loading, setLoading] = useState(false);

  const fundIds = scenario ? Object.keys(scenario.portfolio) : [];

  useEffect(() => {
    if (fundIds.length > 0 && !selectedFundId) {
      setSelectedFundId(fundIds[0]);
    }
  }, [scenario]);

  useEffect(() => {
    if (!selectedFundId) return;
    setLoading(true);
    fetch(`/api/bridge/${selectedFundId}`)
      .then((r) => r.json())
      .then((data) => setBridge(data.error ? null : data))
      .catch((err) => {
        console.error(err);
        setBridge(null);
      })
      .finally(() => setLoading(false));
  }, [selectedFundId]);

  if (!scenario) {
    return (
      <div className="stack">
        <div className="section-header">
          <p className="eyebrow mono">02 -- Valuation Walk</p>
          <h2 className="serif section-title">NAV Bridge</h2>
        </div>
        <div className="empty-state">
          <p className="serif muted">Load a scenario from the Dashboard to view NAV bridges.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stack">
      <div className="section-header">
        <p className="eyebrow mono">02 -- Valuation Walk</p>
        <h2 className="serif section-title">NAV Bridge</h2>
      </div>

      <div className="row controls-row">
        <div className="stack">
          <p className="metric-label">Fund</p>
          <select
            className="select-input mono"
            value={selectedFundId || ""}
            onChange={(e) => setSelectedFundId(e.target.value)}
          >
            {fundIds.map((fid) => (
              <option key={fid} value={fid}>
                {fid} -- {scenario.portfolio[fid].fund_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && <p className="muted mono small">Loading bridge...</p>}

      {bridge && (
        <div className="card">
          <table className="data-table bridge-table">
            <thead>
              <tr>
                <th>Step</th>
                <th className="amount-col">Amount</th>
                <th>Explanation</th>
              </tr>
            </thead>
            <tbody>
              {BRIDGE_ORDER.map((key) => {
                const meta = BRIDGE_META[key];
                const value = bridge[key];
                return (
                  <tr
                    key={key}
                    className={`bridge-row bridge-row--${meta.accent} ${meta.isSubtotal ? "bridge-row--subtotal" : ""}`}
                  >
                    <td className="bridge-label">{meta.label}</td>
                    <td className="mono amount-col">{formatAmount(value)}</td>
                    <td className="muted small">{meta.explain}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

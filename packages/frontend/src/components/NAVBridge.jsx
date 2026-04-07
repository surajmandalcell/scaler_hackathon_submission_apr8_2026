import { useEffect, useState } from "react";

const BRIDGE_META = {
  beginning_nav: {
    label: "Opening Value",
    explain: "Where the fund started this period",
    tone: "subtotal",
  },
  contribution: {
    label: "(+) Capital Called",
    explain: "New capital deployed into properties",
    tone: "positive",
  },
  disposition: {
    label: "(−) Sales Proceeds",
    explain: "Cash received from property sales",
    tone: "negative",
  },
  income: {
    label: "(+) Income Received",
    explain: "Rental and operating income collected",
    tone: "positive",
  },
  cashflow_adjusted_nav: {
    label: "= Cash-Adjusted Value",
    explain: "NAV after all cash movements",
    tone: "subtotal",
  },
  income_reversal: {
    label: "(−) Income Reversal",
    explain: "Income removed from valuation (not a loss)",
    tone: "negative",
  },
  write_up_down: {
    label: "(±) Value Change",
    explain: "Net property valuation change (the plug)",
    tone: "positive",
  },
  ending_nav: {
    label: "= Closing Value",
    explain: "Fund value at end of period",
    tone: "subtotal",
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
  if (n === undefined || n === null) return "—";
  const sign = n < 0 ? "−" : "";
  const abs = Math.abs(n);
  return `${sign}$${abs.toFixed(2)}M`;
}

export default function NAVBridge({ scenario }) {
  const [selectedFundId, setSelectedFundId] = useState(null);
  const [bridge, setBridge] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fundIds = scenario ? Object.keys(scenario.portfolio) : [];

  useEffect(() => {
    if (fundIds.length > 0 && (!selectedFundId || !fundIds.includes(selectedFundId))) {
      setSelectedFundId(fundIds[0]);
    }
    if (fundIds.length === 0) {
      setSelectedFundId(null);
      setBridge(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario]);

  useEffect(() => {
    if (!selectedFundId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetch(`/api/bridge/${selectedFundId}`)
      .then((r) => r.json())
      .then((data) => {
        if (cancelled) return;
        if (data.error) {
          setError(data.error);
          setBridge(null);
        } else {
          setBridge(data);
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message || "Failed to fetch bridge");
        setBridge(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedFundId]);

  if (!scenario) {
    return (
      <div className="md-stack-lg">
        <div className="md-stack-sm">
          <span className="md-eyebrow">02 — Valuation Walk</span>
          <h2 className="md-section-title">NAV Bridge</h2>
        </div>
        <div className="md-empty">
          <span className="md-empty-title">No scenario loaded</span>
          <span className="md-empty-text">
            Load a scenario from the Dashboard to inspect its 8-line NAV bridge.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="md-stack-lg">
      <div className="md-stack-sm">
        <span className="md-eyebrow">02 — Valuation Walk</span>
        <h2 className="md-section-title">NAV Bridge</h2>
        <p className="md-body-large md-on-surface-variant" style={{ maxWidth: 640 }}>
          Walks the fund value from beginning to ending NAV through each
          cashflow and revaluation. Eight rows. The agent's job is to
          reconcile every line within tolerance.
        </p>
      </div>

      <div className="md-field" style={{ maxWidth: 420 }}>
        <label className="md-field-label" htmlFor="bridge-fund-select">
          Fund
        </label>
        <select
          id="bridge-fund-select"
          className="md-select"
          value={selectedFundId || ""}
          onChange={(e) => setSelectedFundId(e.target.value)}
        >
          {fundIds.map((fid) => (
            <option key={fid} value={fid}>
              {fid} — {scenario.portfolio[fid].fund_name}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <p className="md-body-medium md-on-surface-variant">Loading bridge…</p>
      )}

      {error && (
        <div className="md-card" style={{ background: "var(--md-error-container)" }}>
          <p style={{ color: "var(--md-on-error-container)" }}>{error}</p>
        </div>
      )}

      {bridge && !loading && (
        <div className="md-card md-fade-in" style={{ padding: 0, overflow: "hidden" }}>
          <div className="md-table-wrap" style={{ background: "transparent", borderRadius: 0 }}>
            <table className="md-table">
              <thead>
                <tr>
                  <th>Step</th>
                  <th className="md-num-col">Amount</th>
                  <th>Explanation</th>
                </tr>
              </thead>
              <tbody>
                {BRIDGE_ORDER.map((key) => {
                  const meta = BRIDGE_META[key];
                  const value = bridge[key];
                  const isSubtotal = meta.tone === "subtotal";
                  const rowStyle = isSubtotal
                    ? { background: "var(--md-secondary-container)" }
                    : undefined;
                  const labelColor = isSubtotal
                    ? { color: "var(--md-on-secondary-container)", fontWeight: 600 }
                    : undefined;
                  return (
                    <tr key={key} style={rowStyle}>
                      <td>
                        <span style={labelColor}>{meta.label}</span>
                      </td>
                      <td
                        className="md-num"
                        style={
                          isSubtotal
                            ? {
                                color: "var(--md-on-secondary-container)",
                                fontWeight: 600,
                                fontSize: "var(--md-title-medium)",
                              }
                            : undefined
                        }
                      >
                        {formatAmount(value)}
                      </td>
                      <td
                        className="md-body-small md-on-surface-variant"
                        style={
                          isSubtotal
                            ? {
                                color: "var(--md-on-secondary-container)",
                                opacity: 0.85,
                              }
                            : undefined
                        }
                      >
                        {meta.explain}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

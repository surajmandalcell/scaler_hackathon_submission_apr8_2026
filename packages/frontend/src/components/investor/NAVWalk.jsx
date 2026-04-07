import { useEffect, useState } from "react";

// Plain-English labels + explanations for the 8 line items. Ported from the
// old investor/ui.py:134-164. These phrasings are deliberately non-technical
// so an LP with no accounting background can follow the walk.
const BRIDGE_META = {
  beginning_nav: {
    label: "Opening Value",
    explain: "Where the fund started this period",
  },
  contribution: {
    label: "(+) Capital Called",
    explain: "New capital called from investors",
  },
  disposition: {
    label: "(−) Sales Proceeds",
    explain: "Proceeds received from property sales",
  },
  income: {
    label: "(+) Income Received",
    explain: "Rent and yield collected",
  },
  cashflow_adjusted_nav: {
    label: "= Cash-Adjusted Value",
    explain: "NAV after all cash movements",
  },
  income_reversal: {
    label: "(−) Income Reversal",
    explain: "Income added back (already counted in the valuation)",
  },
  write_up_down: {
    label: "(+/−) Property Value Change",
    explain: "Change in property values (appraiser estimate)",
  },
  ending_nav: {
    label: "= Closing Value",
    explain: "Fund value at end of period",
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

function fmtUsdM(v) {
  if (v == null || Number.isNaN(Number(v))) return "—";
  return `$${Number(v).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}M`;
}

export default function NAVWalk({ scenario }) {
  const portfolio = scenario?.portfolio || {};
  const fundIds = Object.keys(portfolio);
  const [fundId, setFundId] = useState(fundIds[0] || "");
  const [bridge, setBridge] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Reset selected fund if the scenario changed
    if (fundIds.length > 0 && !fundIds.includes(fundId)) {
      setFundId(fundIds[0]);
    }
  }, [scenario]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!fundId) return;
    let alive = true;
    setLoading(true);
    setError(null);
    fetch(`/api/bridge/${encodeURIComponent(fundId)}`)
      .then((r) => r.json())
      .then((data) => {
        if (!alive) return;
        if (data.error) {
          setError(data.error);
          setBridge(null);
        } else {
          setBridge(data);
        }
      })
      .catch((err) => alive && setError(err.message))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [fundId]);

  if (fundIds.length === 0) {
    return (
      <div className="md-empty">
        <p className="md-empty-title">No funds loaded</p>
        <p className="md-empty-text">Load a scenario first.</p>
      </div>
    );
  }

  return (
    <div className="md-stack-lg md-reveal">
      <section className="md-stack-sm">
        <span className="md-eyebrow">Step-by-step</span>
        <h3 className="md-headline-small">How did the fund value change?</h3>
        <p className="md-body-medium md-on-surface-variant">
          This walk moves from the opening value to the closing value, one line
          at a time. Graded in every mode.
        </p>
      </section>

      <div className="md-row">
        <label className="md-field" style={{ maxWidth: 340, flex: 1 }}>
          <span className="md-field-label">Select fund</span>
          <select
            className="md-select"
            value={fundId}
            onChange={(e) => setFundId(e.target.value)}
          >
            {fundIds.map((fid) => (
              <option key={fid} value={fid}>
                {portfolio[fid]?.fund_name || fid}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading && <p className="md-body-medium md-on-surface-variant">Loading walk…</p>}

      {error && (
        <div className="md-card" style={{ background: "var(--md-error-container)" }}>
          <p style={{ color: "var(--md-on-error-container)" }}>{error}</p>
        </div>
      )}

      {bridge && !error && (
        <div className="md-table-wrap">
          <table className="md-table md-table-reveal">
            <thead>
              <tr>
                <th>Step</th>
                <th style={{ textAlign: "right" }}>Amount</th>
                <th>What this means</th>
              </tr>
            </thead>
            <tbody>
              {BRIDGE_ORDER.map((key) => {
                const meta = BRIDGE_META[key];
                const isSubtotal = key === "cashflow_adjusted_nav" || key === "ending_nav";
                return (
                  <tr key={key}>
                    <td>
                      {isSubtotal ? <strong>{meta.label}</strong> : meta.label}
                    </td>
                    <td className="md-mono" style={{ textAlign: "right" }}>
                      {isSubtotal ? <strong>{fmtUsdM(bridge[key])}</strong> : fmtUsdM(bridge[key])}
                    </td>
                    <td className="md-body-small md-on-surface-variant">{meta.explain}</td>
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

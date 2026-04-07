import { useEffect, useState } from "react";

function fmtUsdM(v) {
  if (v == null || Number.isNaN(Number(v))) return "—";
  return `$${Number(v).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}M`;
}

export default function ITDSummary({ scenario }) {
  const portfolio = scenario?.portfolio || {};
  const fundIds = Object.keys(portfolio);
  const [fundId, setFundId] = useState(fundIds[0] || "");
  const [cashflows, setCashflows] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (fundIds.length > 0 && !fundIds.includes(fundId)) {
      setFundId(fundIds[0]);
    }
  }, [scenario]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!fundId) return;
    let alive = true;
    setLoading(true);
    fetch(`/api/cashflows/${encodeURIComponent(fundId)}`)
      .then((r) => r.json())
      .then((data) => alive && setCashflows(data))
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

  const fund = portfolio[fundId];
  const unrealized = fund?.ending_nav ?? 0;
  const totalIn = cashflows?.total_contribution ?? 0;
  const totalDisp = cashflows?.total_disposition ?? 0;
  const totalInc = cashflows?.total_income ?? 0;
  const totalOut = totalDisp + totalInc;
  const totalValue = totalOut + unrealized;

  const rows = [
    {
      label: "Total Capital Invested (ITD)",
      amount: fmtUsdM(totalIn),
      explain: "All capital calls since fund inception",
    },
    {
      label: "Total Cash Received (ITD)",
      amount: fmtUsdM(totalDisp),
      explain: "Property sale proceeds returned to investors",
    },
    {
      label: "Total Income Received (ITD)",
      amount: fmtUsdM(totalInc),
      explain: "Rent and distributions paid out",
    },
    {
      label: "Total Cash Returned (ITD)",
      amount: fmtUsdM(totalOut),
      explain: "Sales + Income combined",
      subtotal: true,
    },
    {
      label: "Current Fund Value (Unrealized)",
      amount: fmtUsdM(unrealized),
      explain: "Appraiser-estimated value of remaining properties",
    },
    {
      label: "Total Value (Cash + Unrealized)",
      amount: fmtUsdM(totalValue),
      explain: "What investors have received + what remains invested",
      subtotal: true,
    },
  ];

  return (
    <div className="md-stack-lg md-reveal">
      <section className="md-stack-sm">
        <span className="md-eyebrow">Inception to date</span>
        <h3 className="md-headline-small">Where the money went and came back</h3>
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

      {loading && <p className="md-body-medium md-on-surface-variant">Loading…</p>}

      {cashflows && (
        <div className="md-table-wrap">
          <table className="md-table md-table-reveal">
            <thead>
              <tr>
                <th>Line</th>
                <th style={{ textAlign: "right" }}>Amount</th>
                <th>What this means</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  <td>{r.subtotal ? <strong>{r.label}</strong> : r.label}</td>
                  <td className="md-mono" style={{ textAlign: "right" }}>
                    {r.subtotal ? <strong>{r.amount}</strong> : r.amount}
                  </td>
                  <td className="md-body-small md-on-surface-variant">{r.explain}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";

function fmtUsdM(v) {
  if (v == null || Number.isNaN(Number(v))) return "—";
  return `$${Number(v).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}M`;
}

function fmtPct(v) {
  if (v == null) return "—";
  return `${(v * 100).toFixed(0)}%`;
}

export default function Properties({ scenario }) {
  const portfolio = scenario?.portfolio || {};
  const fundIds = Object.keys(portfolio);
  const [fundId, setFundId] = useState(fundIds[0] || "");
  const [deals, setDeals] = useState(null);
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
    fetch(`/api/deals/${encodeURIComponent(fundId)}`)
      .then((r) => r.json())
      .then((data) => {
        if (!alive) return;
        setDeals(data.deals || []);
      })
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
    <div className="md-stack-lg">
      <section className="md-stack-sm">
        <span className="md-eyebrow">Holdings</span>
        <h3 className="md-headline-small">Properties in this fund</h3>
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

      {deals && deals.length === 0 && (
        <p className="md-body-medium md-on-surface-variant">No properties on file for this fund.</p>
      )}

      {deals && deals.length > 0 && (
        <div className="md-table-wrap">
          <table className="md-table">
            <thead>
              <tr>
                <th>Property</th>
                <th>Sector</th>
                <th>Location</th>
                <th style={{ textAlign: "right" }}>Fund share</th>
                <th style={{ textAlign: "right" }}>Capital invested</th>
                <th style={{ textAlign: "right" }}>Cash returned</th>
              </tr>
            </thead>
            <tbody>
              {deals.map((d) => (
                <tr key={d.deal_id}>
                  <td><strong>{d.property_name}</strong></td>
                  <td>{d.sector || "—"}</td>
                  <td>{d.location || "—"}</td>
                  <td className="md-mono" style={{ textAlign: "right" }}>
                    {fmtPct(d.ownership_pct)}
                  </td>
                  <td className="md-mono" style={{ textAlign: "right" }}>
                    {fmtUsdM(d.invested)}
                  </td>
                  <td className="md-mono" style={{ textAlign: "right" }}>
                    {fmtUsdM(d.received)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

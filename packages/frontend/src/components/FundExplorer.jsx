import { useState, useEffect } from "react";

function formatMoney(n) {
  if (n === undefined || n === null) return "-";
  return `$${n.toFixed(2)}M`;
}

function formatPct(n) {
  if (n === undefined || n === null) return "-";
  return `${(n * 100).toFixed(0)}%`;
}

export default function FundExplorer({ scenario }) {
  const [selectedFundId, setSelectedFundId] = useState(null);
  const [deals, setDeals] = useState(null);
  const [cashflows, setCashflows] = useState(null);
  const [sectors, setSectors] = useState(null);
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
    Promise.all([
      fetch(`/api/deals/${selectedFundId}`).then((r) => r.json()),
      fetch(`/api/cashflows/${selectedFundId}`).then((r) => r.json()),
      fetch(`/api/sectors`).then((r) => r.json()),
    ])
      .then(([d, c, s]) => {
        setDeals(d.error ? null : d);
        setCashflows(c.error ? null : c);
        setSectors(s);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedFundId]);

  if (!scenario) {
    return (
      <div className="stack">
        <div className="section-header">
          <p className="eyebrow mono">03 -- Portfolio</p>
          <h2 className="serif section-title">Fund Explorer</h2>
        </div>
        <div className="empty-state">
          <p className="serif muted">Load a scenario from the Dashboard to explore funds.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stack">
      <div className="section-header">
        <p className="eyebrow mono">03 -- Portfolio</p>
        <h2 className="serif section-title">Fund Explorer</h2>
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

      {loading && <p className="muted mono small">Loading fund data...</p>}

      {cashflows && (
        <div className="grid-3">
          <div className="card card-accent-emerald">
            <p className="metric-label">Total Contribution</p>
            <p className="metric-number">{formatMoney(cashflows.total_contribution)}</p>
            <p className="muted small">Capital deployed</p>
          </div>
          <div className="card card-accent-blue">
            <p className="metric-label">Total Disposition</p>
            <p className="metric-number">{formatMoney(cashflows.total_disposition)}</p>
            <p className="muted small">Sale proceeds</p>
          </div>
          <div className="card card-accent-emerald">
            <p className="metric-label">Total Income</p>
            <p className="metric-number">{formatMoney(cashflows.total_income)}</p>
            <p className="muted small">Rental / operating</p>
          </div>
        </div>
      )}

      {deals && (
        <div className="stack">
          <div className="section-header">
            <p className="eyebrow mono">Deals</p>
          </div>
          <div className="card">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Property</th>
                  <th>Sector</th>
                  <th>Location</th>
                  <th className="amount-col">Ownership</th>
                  <th className="amount-col">Invested</th>
                  <th className="amount-col">Received</th>
                </tr>
              </thead>
              <tbody>
                {deals.deals.map((deal) => (
                  <tr key={deal.deal_id}>
                    <td>{deal.property_name}</td>
                    <td className="muted">{deal.sector}</td>
                    <td className="muted small">{deal.location}</td>
                    <td className="mono amount-col">{formatPct(deal.ownership_pct)}</td>
                    <td className="mono amount-col">{formatMoney(deal.invested)}</td>
                    <td className="mono amount-col positive">{formatMoney(deal.received)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {sectors && Object.keys(sectors).length > 0 && (
        <div className="stack">
          <div className="section-header">
            <p className="eyebrow mono">Sector Breakdown</p>
          </div>
          <div className="grid-3">
            {Object.entries(sectors).map(([sector, data]) => (
              <div key={sector} className="card card-accent-blue">
                <p className="metric-label">{sector}</p>
                <h4 className="serif">{data.deal_count} deals</h4>
                <div className="divider"></div>
                <div className="row">
                  <div>
                    <p className="metric-label">Invested</p>
                    <p className="metric-number small">{formatMoney(data.total_invested)}</p>
                  </div>
                  <div>
                    <p className="metric-label">Received</p>
                    <p className="metric-number small positive">{formatMoney(data.total_received)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

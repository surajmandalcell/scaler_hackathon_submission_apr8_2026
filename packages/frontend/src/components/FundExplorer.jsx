import { useEffect, useState } from "react";

function formatMoney(n) {
  if (n === undefined || n === null) return "—";
  return `$${Number(n).toFixed(2)}M`;
}

function formatPct(n) {
  if (n === undefined || n === null) return "—";
  return `${Math.round(Number(n) * 100)}%`;
}

export default function FundExplorer({ scenario }) {
  const [selectedFundId, setSelectedFundId] = useState(null);
  const [deals, setDeals] = useState(null);
  const [cashflows, setCashflows] = useState(null);
  const [sectors, setSectors] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fundIds = scenario ? Object.keys(scenario.portfolio) : [];

  useEffect(() => {
    if (fundIds.length > 0 && (!selectedFundId || !fundIds.includes(selectedFundId))) {
      setSelectedFundId(fundIds[0]);
    }
    if (fundIds.length === 0) {
      setSelectedFundId(null);
      setDeals(null);
      setCashflows(null);
      setSectors(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario]);

  useEffect(() => {
    if (!selectedFundId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      fetch(`/api/deals/${selectedFundId}`).then((r) => r.json()),
      fetch(`/api/cashflows/${selectedFundId}`).then((r) => r.json()),
      fetch(`/api/sectors`).then((r) => r.json()),
    ])
      .then(([dealsData, cashflowsData, sectorsData]) => {
        if (cancelled) return;
        setDeals(dealsData.error ? null : dealsData);
        setCashflows(cashflowsData.error ? null : cashflowsData);
        setSectors(sectorsData);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message || "Failed to load fund data");
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
          <span className="md-eyebrow">03 — Underlying</span>
          <h2 className="md-section-title">Fund Explorer</h2>
        </div>
        <div className="md-empty">
          <span className="md-empty-title">No scenario loaded</span>
          <span className="md-empty-text">
            Load a scenario from the Dashboard to browse deals, cashflows, and
            sector breakdowns.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="md-stack-lg">
      <div className="md-stack-sm">
        <span className="md-eyebrow">03 — Underlying</span>
        <h2 className="md-section-title">Fund Explorer</h2>
        <p className="md-body-large md-on-surface-variant" style={{ maxWidth: 640 }}>
          Drill into each fund's properties, cashflow records, and sector
          mix. This is the data the agent has to work with.
        </p>
      </div>

      <div className="md-field" style={{ maxWidth: 420 }}>
        <label className="md-field-label" htmlFor="explorer-fund-select">
          Fund
        </label>
        <select
          id="explorer-fund-select"
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
        <p className="md-body-medium md-on-surface-variant">Loading fund data…</p>
      )}

      {error && (
        <div className="md-card" style={{ background: "var(--md-error-container)" }}>
          <p style={{ color: "var(--md-on-error-container)" }}>{error}</p>
        </div>
      )}

      {/* Cashflow totals */}
      {cashflows && !loading && (
        <div className="md-grid md-grid-3 md-fade-in">
          <div className="md-card md-card-tonal-secondary">
            <div className="md-stack-sm">
              <span className="md-metric-label" style={{ color: "var(--md-on-secondary-container)" }}>
                Capital deployed
              </span>
              <span
                className="md-metric-value-lg"
                style={{ color: "var(--md-on-secondary-container)" }}
              >
                {formatMoney(cashflows.total_contribution)}
              </span>
              <span className="md-body-small" style={{ color: "var(--md-on-secondary-container)", opacity: 0.8 }}>
                Total contributions
              </span>
            </div>
          </div>
          <div className="md-card md-card-tonal-tertiary">
            <div className="md-stack-sm">
              <span className="md-metric-label" style={{ color: "var(--md-on-tertiary-container)" }}>
                Sale proceeds
              </span>
              <span
                className="md-metric-value-lg"
                style={{ color: "var(--md-on-tertiary-container)" }}
              >
                {formatMoney(cashflows.total_disposition)}
              </span>
              <span className="md-body-small" style={{ color: "var(--md-on-tertiary-container)", opacity: 0.8 }}>
                Total dispositions
              </span>
            </div>
          </div>
          <div className="md-card md-card-tonal-primary">
            <div className="md-stack-sm">
              <span className="md-metric-label" style={{ color: "var(--md-on-primary-container)" }}>
                Income
              </span>
              <span
                className="md-metric-value-lg"
                style={{ color: "var(--md-on-primary-container)" }}
              >
                {formatMoney(cashflows.total_income)}
              </span>
              <span className="md-body-small" style={{ color: "var(--md-on-primary-container)", opacity: 0.8 }}>
                Rental / operating
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Deals table */}
      {deals && !loading && (
        <section className="md-stack">
          <div className="md-stack-sm">
            <span className="md-eyebrow">Deals</span>
            <h3 className="md-headline-small">
              {deals.deals.length}{" "}
              {deals.deals.length === 1 ? "property" : "properties"}
            </h3>
          </div>

          <div className="md-card md-fade-in" style={{ padding: 0, overflow: "hidden" }}>
            <div className="md-table-wrap" style={{ background: "transparent", borderRadius: 0 }}>
              <table className="md-table">
                <thead>
                  <tr>
                    <th>Property</th>
                    <th>Sector</th>
                    <th>Location</th>
                    <th className="md-num-col">Ownership</th>
                    <th className="md-num-col">Invested</th>
                    <th className="md-num-col">Received</th>
                  </tr>
                </thead>
                <tbody>
                  {deals.deals.map((deal) => (
                    <tr key={deal.deal_id}>
                      <td>
                        <span className="md-title-small">{deal.property_name}</span>
                      </td>
                      <td>
                        <span className="md-badge md-badge-primary">{deal.sector}</span>
                      </td>
                      <td className="md-body-small md-on-surface-variant">
                        {deal.location}
                      </td>
                      <td className="md-num">{formatPct(deal.ownership_pct)}</td>
                      <td className="md-num">{formatMoney(deal.invested)}</td>
                      <td className="md-num md-pos">{formatMoney(deal.received)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* Sector breakdown */}
      {sectors && Object.keys(sectors).length > 0 && !loading && (
        <section className="md-stack">
          <div className="md-stack-sm">
            <span className="md-eyebrow">Sector mix</span>
            <h3 className="md-headline-small">By property type</h3>
          </div>

          <div className="md-grid md-grid-3">
            {Object.entries(sectors).map(([sector, data]) => (
              <div key={sector} className="md-card md-fade-in">
                <div className="md-stack-sm">
                  <div className="md-row-spread">
                    <span className="md-title-medium">{sector}</span>
                    <span className="md-badge">
                      {data.deal_count} {data.deal_count === 1 ? "deal" : "deals"}
                    </span>
                  </div>
                  <div className="md-divider" />
                  <div className="md-row" style={{ gap: "var(--md-space-7)" }}>
                    <div className="md-metric">
                      <span className="md-metric-label">Invested</span>
                      <span className="md-metric-value">
                        {formatMoney(data.total_invested)}
                      </span>
                    </div>
                    <div className="md-metric">
                      <span className="md-metric-label">Received</span>
                      <span className="md-metric-value md-pos">
                        {formatMoney(data.total_received)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

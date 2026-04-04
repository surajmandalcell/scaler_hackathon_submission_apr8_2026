function daysUntil(currentDate, expiryDate) {
  return Math.ceil((new Date(expiryDate) - new Date(currentDate)) / 86400000);
}

function urgency(days) {
  if (days <= 1) return "var(--danger)";
  if (days <= 3) return "var(--warn)";
  return "var(--t4)";
}

export default function FridgeView({ inventory, currentDate, horizon, householdSize, restrictions }) {
  const sorted = [...inventory].sort((a, b) => a.expiry_date.localeCompare(b.expiry_date));

  return (
    <section className="enter">
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 16 }}>
        <h2 style={{ fontFamily: "var(--serif)", fontWeight: 300, fontSize: "1.25rem", color: "var(--t1)" }}>
          Inventory
        </h2>
        <div style={{ display: "flex", gap: 16, fontFamily: "var(--mono)", fontSize: "0.72rem", color: "var(--t3)" }}>
          <span>{inventory.length} items</span>
          <span>{horizon}d horizon</span>
          <span>{householdSize} people</span>
          {restrictions.length > 0 && (
            <span style={{ color: "var(--accent)" }}>{restrictions.join(", ")}</span>
          )}
        </div>
      </div>

      {/* Table */}
      <div style={{
        background: "var(--bg-raised)", border: "1px solid var(--line)",
        borderRadius: "var(--r-lg)", overflow: "hidden",
      }}>
        {/* Table header */}
        <div style={{
          display: "grid", gridTemplateColumns: "1fr 100px 80px",
          padding: "12px 24px", borderBottom: "1px solid var(--line)",
          fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--t4)",
          textTransform: "uppercase", letterSpacing: "0.06em",
        }}>
          <span>Item</span>
          <span style={{ textAlign: "right" }}>Quantity</span>
          <span style={{ textAlign: "right" }}>Expires</span>
        </div>

        {/* Rows */}
        {sorted.map((item, i) => {
          const days = daysUntil(currentDate, item.expiry_date);
          const urgent = days <= 2;

          return (
            <div key={item.name} className="enter" style={{
              display: "grid", gridTemplateColumns: "1fr 100px 80px",
              padding: "12px 24px", alignItems: "center",
              borderBottom: i < sorted.length - 1 ? "1px solid var(--line)" : "none",
              background: urgent ? "rgba(160, 75, 58, 0.04)" : "transparent",
              animationDelay: `${i * 20}ms`,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{
                  width: 3, height: 20, borderRadius: 2,
                  background: urgency(days), flexShrink: 0,
                }} />
                <span style={{
                  fontFamily: "var(--sans)", fontSize: "0.85rem",
                  color: "var(--t1)", fontWeight: 400,
                }}>
                  {item.name.replace(/_/g, " ")}
                </span>
                <span style={{
                  fontFamily: "var(--mono)", fontSize: "0.65rem",
                  color: "var(--t4)", marginLeft: 4,
                }}>
                  {item.category}
                </span>
              </div>
              <span style={{
                fontFamily: "var(--mono)", fontSize: "0.8rem",
                color: "var(--t2)", textAlign: "right",
              }}>
                {Math.round(item.quantity)}{item.unit}
              </span>
              <span style={{
                fontFamily: "var(--mono)", fontSize: "0.78rem",
                color: urgency(days), textAlign: "right", fontWeight: urgent ? 500 : 400,
              }}>
                {days <= 0 ? "expired" : days === 1 ? "1d" : `${days}d`}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

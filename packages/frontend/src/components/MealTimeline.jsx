export default function MealTimeline({ consumptionLog, nutritionLog, horizon, expiryEvents }) {
  if (!consumptionLog) return null;

  const expirySet = new Set(expiryEvents || []);
  const items = Object.entries(consumptionLog)
    .sort(([, a], [, b]) => b - a)
    .map(([name, qty]) => ({ name, consumed: Math.round(qty * 10) / 10, expired: expirySet.has(name) }));
  const maxQty = Math.max(...items.map((i) => i.consumed), 1);

  return (
    <section className="enter" style={{
      background: "var(--bg-raised)", border: "1px solid var(--line)",
      borderRadius: "var(--r-lg)", padding: "28px 32px",
    }}>
      {/* Nutrition grid */}
      <div style={{ marginBottom: 28 }}>
        <Label>Daily Nutrition</Label>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 8 }}>
          {Array.from({ length: horizon }, (_, i) => {
            const day = i + 1;
            const cats = new Set(nutritionLog?.[day] || nutritionLog?.[String(day)] || []);
            const p = cats.has("protein");
            const c = cats.has("carb");
            const v = cats.has("vegetable");
            const balanced = p && c && v;
            const any = cats.size > 0;

            return (
              <div key={day} style={{
                width: 38, padding: "5px 0", textAlign: "center",
                borderRadius: "var(--r)", border: `1px solid ${balanced ? "rgba(107,155,90,0.3)" : "var(--line)"}`,
                background: balanced ? "rgba(107,155,90,0.06)" : "transparent",
              }}>
                <div style={{ fontFamily: "var(--mono)", fontSize: "0.6rem", color: "var(--t4)" }}>
                  {day}
                </div>
                <div style={{ display: "flex", justifyContent: "center", gap: 2, marginTop: 3 }}>
                  <Dot on={p} /><Dot on={c} /><Dot on={v} />
                </div>
              </div>
            );
          })}
        </div>
        <div style={{ display: "flex", gap: 14, marginTop: 8, fontFamily: "var(--mono)", fontSize: "0.6rem", color: "var(--t4)" }}>
          <span>P / C / V per day</span>
          <span style={{ color: "var(--ok)" }}>balanced = all three</span>
        </div>
      </div>

      {/* Consumption bars */}
      <div>
        <Label>Consumption ({items.length} items)</Label>
        <div style={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 8 }}>
          {items.map((item) => (
            <div key={item.name} style={{
              display: "grid", gridTemplateColumns: "160px 1fr 56px",
              gap: 12, alignItems: "center", padding: "3px 0",
            }}>
              <span style={{
                fontFamily: "var(--mono)", fontSize: "0.75rem",
                color: item.expired ? "var(--danger)" : "var(--t2)",
                textDecoration: item.expired ? "line-through" : "none",
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
              }}>
                {item.name.replace(/_/g, " ")}
              </span>
              <div style={{ height: 4, borderRadius: 2, background: "var(--bg-surface)", overflow: "hidden" }}>
                <div style={{
                  height: "100%", borderRadius: 2,
                  width: `${(item.consumed / maxQty) * 100}%`,
                  background: item.expired ? "var(--danger)" : "var(--t3)",
                  transition: "width 0.4s ease-out",
                }} />
              </div>
              <span style={{
                fontFamily: "var(--mono)", fontSize: "0.7rem",
                color: "var(--t4)", textAlign: "right",
              }}>
                {item.consumed}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Wasted */}
      {expiryEvents?.length > 0 && (() => {
        const fullyWasted = expiryEvents.filter((e) => !consumptionLog[e]);
        if (!fullyWasted.length) return null;
        return (
          <div style={{ marginTop: 20, paddingTop: 14, borderTop: "1px solid var(--line)" }}>
            <Label danger>Wasted ({fullyWasted.length})</Label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 6 }}>
              {fullyWasted.map((name) => (
                <span key={name} style={{
                  fontFamily: "var(--mono)", fontSize: "0.7rem", color: "var(--danger)",
                  padding: "2px 8px", borderRadius: "var(--r)",
                  background: "rgba(160,75,58,0.06)", border: "1px solid rgba(160,75,58,0.15)",
                }}>
                  {name.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          </div>
        );
      })()}
    </section>
  );
}

function Label({ children, danger }) {
  return (
    <div style={{
      fontFamily: "var(--mono)", fontSize: "0.62rem",
      color: danger ? "var(--danger)" : "var(--t4)",
      textTransform: "uppercase", letterSpacing: "0.06em",
    }}>
      {children}
    </div>
  );
}

function Dot({ on }) {
  return (
    <div style={{
      width: 5, height: 5, borderRadius: "50%",
      background: on ? "var(--t2)" : "var(--line)",
    }} />
  );
}

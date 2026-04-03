import React from "react";

export default function MealTimeline({
  consumptionLog,
  nutritionLog,
  horizon,
  expiryEvents,
}) {
  if (!consumptionLog) return null;

  const expirySet = new Set(expiryEvents || []);

  // Build per-item consumption data
  const items = Object.entries(consumptionLog)
    .sort(([, a], [, b]) => b - a)
    .map(([name, qty]) => ({
      name,
      consumed: Math.round(qty * 10) / 10,
      expired: expirySet.has(name),
    }));

  return (
    <div
      className="fade-in"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: "28px",
        animationDelay: "0.2s",
      }}
    >
      <h3
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "1.3rem",
          fontWeight: 400,
          marginBottom: 20,
        }}
      >
        Consumption Summary
      </h3>

      {/* Day-by-day nutrition */}
      <div style={{ marginBottom: 24 }}>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.65rem",
            color: "var(--text-muted)",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            marginBottom: 10,
          }}
        >
          Daily Nutrition Balance
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {Array.from({ length: horizon }, (_, i) => {
            const day = i + 1;
            const cats = new Set(nutritionLog?.[day] || nutritionLog?.[String(day)] || []);
            const hasProtein = cats.has("protein");
            const hasCarb = cats.has("carb");
            const hasVeg = cats.has("vegetable");
            const balanced = hasProtein && hasCarb && hasVeg;
            const partial = cats.size > 0;

            return (
              <div
                key={day}
                style={{
                  width: 44,
                  textAlign: "center",
                  padding: "6px 4px",
                  borderRadius: 6,
                  border: `1px solid ${balanced ? "var(--green-fresh)" : partial ? "var(--yellow-warning)" : "var(--border)"}`,
                  background: balanced
                    ? "rgba(74, 222, 128, 0.08)"
                    : partial
                    ? "rgba(250, 204, 21, 0.05)"
                    : "transparent",
                }}
              >
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.65rem",
                    color: "var(--text-muted)",
                  }}
                >
                  D{day}
                </div>
                <div style={{ display: "flex", justifyContent: "center", gap: 2, marginTop: 3 }}>
                  <Dot active={hasProtein} color="var(--red-expired)" title="Protein" />
                  <Dot active={hasCarb} color="var(--yellow-warning)" title="Carb" />
                  <Dot active={hasVeg} color="var(--green-fresh)" title="Vegetable" />
                </div>
              </div>
            );
          })}
        </div>
        <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
          <Legend color="var(--red-expired)" label="Protein" />
          <Legend color="var(--yellow-warning)" label="Carb" />
          <Legend color="var(--green-fresh)" label="Vegetable" />
        </div>
      </div>

      {/* Items consumed */}
      <div>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.65rem",
            color: "var(--text-muted)",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            marginBottom: 10,
          }}
        >
          Items Consumed ({items.length})
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {items.map((item) => {
            const maxQty = Math.max(...items.map((i) => i.consumed), 1);
            const barWidth = (item.consumed / maxQty) * 100;

            return (
              <div
                key={item.name}
                style={{
                  display: "grid",
                  gridTemplateColumns: "160px 1fr 60px",
                  gap: 12,
                  alignItems: "center",
                  padding: "4px 0",
                }}
              >
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.75rem",
                    color: item.expired ? "var(--red-expired)" : "var(--text-secondary)",
                    textDecoration: item.expired ? "line-through" : "none",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {item.name.replace(/_/g, " ")}
                  {item.expired && " (expired)"}
                </span>
                <div
                  style={{
                    height: 6,
                    borderRadius: 3,
                    background: "var(--bg-elevated)",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${barWidth}%`,
                      borderRadius: 3,
                      background: item.expired
                        ? "var(--red-expired)"
                        : "linear-gradient(90deg, var(--green-muted), var(--green-fresh))",
                      transition: "width 0.5s ease-out",
                    }}
                  />
                </div>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.7rem",
                    color: "var(--text-muted)",
                    textAlign: "right",
                  }}
                >
                  {item.consumed}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Expired items not consumed */}
      {expiryEvents && expiryEvents.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.65rem",
              color: "var(--red-expired)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              marginBottom: 8,
            }}
          >
            Wasted Items ({expiryEvents.filter((e) => !consumptionLog[e]).length} fully wasted)
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {expiryEvents
              .filter((e) => !consumptionLog[e])
              .map((name) => (
                <span
                  key={name}
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.7rem",
                    color: "var(--red-expired)",
                    padding: "3px 8px",
                    borderRadius: 4,
                    background: "rgba(239, 68, 68, 0.08)",
                    border: "1px solid rgba(239, 68, 68, 0.2)",
                  }}
                >
                  {name.replace(/_/g, " ")}
                </span>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Dot({ active, color, title }) {
  return (
    <div
      title={title}
      style={{
        width: 6,
        height: 6,
        borderRadius: "50%",
        background: active ? color : "var(--border)",
        transition: "background 0.2s",
      }}
    />
  );
}

function Legend({ color, label }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      <div style={{ width: 6, height: 6, borderRadius: "50%", background: color }} />
      <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", color: "var(--text-muted)" }}>
        {label}
      </span>
    </div>
  );
}

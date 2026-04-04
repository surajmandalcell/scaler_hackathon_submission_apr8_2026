import React from "react";

const CATEGORY_EMOJI = {
  protein: "🥩",
  carb: "🍞",
  vegetable: "🥬",
  dairy: "🧀",
  fruit: "🍎",
  condiment: "🫙",
};

function daysUntilExpiry(currentDate, expiryDate) {
  const curr = new Date(currentDate);
  const exp = new Date(expiryDate);
  return Math.ceil((exp - curr) / (1000 * 60 * 60 * 24));
}

function expiryColor(days) {
  if (days <= 1) return "var(--red-expired)";
  if (days <= 2) return "var(--amber-urgent)";
  if (days <= 4) return "var(--yellow-warning)";
  return "var(--green-fresh)";
}

function expiryBg(days) {
  if (days <= 1) return "rgba(239, 68, 68, 0.08)";
  if (days <= 2) return "rgba(245, 158, 11, 0.06)";
  if (days <= 4) return "rgba(250, 204, 21, 0.04)";
  return "rgba(74, 222, 128, 0.04)";
}

export default function FridgeView({
  inventory,
  currentDate,
  horizon,
  householdSize,
  restrictions,
}) {
  const sorted = [...inventory].sort((a, b) =>
    a.expiry_date.localeCompare(b.expiry_date)
  );

  return (
    <div className="fade-in" style={{ animationDelay: "0.1s" }}>
      {/* Meta bar */}
      <div
        style={{
          display: "flex",
          gap: 24,
          marginBottom: 16,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <h2
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "1.5rem",
            fontWeight: 400,
            color: "var(--text-primary)",
          }}
        >
          Fridge Inventory
        </h2>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          <Tag label="Items" value={inventory.length} />
          <Tag label="Horizon" value={`${horizon}d`} />
          <Tag label="Household" value={householdSize} />
          {restrictions.length > 0 && (
            <Tag
              label="Restrictions"
              value={restrictions.join(", ")}
              accent
            />
          )}
        </div>
      </div>

      {/* Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
          gap: 10,
        }}
      >
        {sorted.map((item, i) => {
          const days = daysUntilExpiry(currentDate, item.expiry_date);
          const color = expiryColor(days);
          const isUrgent = days <= 2;

          return (
            <div
              key={item.name}
              className="fade-in"
              style={{
                animationDelay: `${i * 30}ms`,
                background: expiryBg(days),
                border: `1px solid ${isUrgent ? color : "var(--border)"}`,
                borderRadius: "var(--radius-sm)",
                padding: "14px 16px",
                transition: "all 0.2s",
                cursor: "default",
                animation: isUrgent ? "pulse-warm 2.5s ease-in-out infinite" : undefined,
                position: "relative",
                overflow: "hidden",
              }}
            >
              {/* Urgency stripe */}
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  width: 3,
                  height: "100%",
                  background: color,
                  borderRadius: "3px 0 0 3px",
                }}
              />

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontSize: "1.1rem" }}>
                    {CATEGORY_EMOJI[item.category] || "📦"}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.8rem",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                    }}
                  >
                    {item.name.replace(/_/g, " ")}
                  </span>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.75rem",
                    color: "var(--text-secondary)",
                  }}
                >
                  {item.quantity}{item.unit}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.7rem",
                    fontWeight: 600,
                    color,
                    padding: "2px 8px",
                    borderRadius: 4,
                    background: `${color}15`,
                  }}
                >
                  {days <= 0 ? "EXPIRED" : days === 1 ? "1 day" : `${days} days`}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Tag({ label, value, accent }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        padding: "4px 10px",
        borderRadius: 6,
        background: accent ? "var(--accent-soft)" : "var(--bg-card)",
        border: `1px solid ${accent ? "var(--border-accent)" : "var(--border)"}`,
      }}
    >
      <span
        style={{
          fontSize: "0.65rem",
          fontFamily: "var(--font-mono)",
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontSize: "0.8rem",
          fontFamily: "var(--font-mono)",
          fontWeight: 600,
          color: accent ? "var(--accent)" : "var(--text-primary)",
        }}
      >
        {value}
      </span>
    </div>
  );
}

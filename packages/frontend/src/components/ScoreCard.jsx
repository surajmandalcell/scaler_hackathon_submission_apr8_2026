import React from "react";

function scoreColor(score) {
  if (score >= 0.8) return "var(--green-fresh)";
  if (score >= 0.5) return "var(--yellow-warning)";
  if (score >= 0.3) return "var(--amber-urgent)";
  return "var(--red-expired)";
}

export default function ScoreCard({ reward, info }) {
  if (!reward) return null;

  const score = reward.score;
  const color = scoreColor(score);
  const pct = Math.round(score * 100);

  return (
    <div
      className="fade-in"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: "32px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background glow */}
      <div
        style={{
          position: "absolute",
          top: -40,
          right: -40,
          width: 200,
          height: 200,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${color}20, transparent 70%)`,
          pointerEvents: "none",
        }}
      />

      <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: 32, alignItems: "center" }}>
        {/* Big score */}
        <div
          style={{
            textAlign: "center",
            animation: "score-reveal 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both",
          }}
        >
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontSize: "4rem",
              fontWeight: 400,
              color,
              lineHeight: 1,
            }}
          >
            {pct}
          </div>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.7rem",
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              marginTop: 4,
            }}
          >
            Grader Score
          </div>
        </div>

        {/* Metrics grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 16 }}>
          <Metric
            label="Waste Rate"
            value={`${Math.round(reward.waste_rate * 100)}%`}
            color={reward.waste_rate > 0.3 ? "var(--red-expired)" : "var(--green-fresh)"}
          />
          <Metric
            label="Nutrition"
            value={`${Math.round(reward.nutrition_score * 100)}%`}
            color={reward.nutrition_score > 0.5 ? "var(--green-fresh)" : "var(--yellow-warning)"}
          />
          <Metric label="Items Used" value={reward.items_used} color="var(--text-primary)" />
          <Metric
            label="Expired"
            value={reward.items_expired}
            color={reward.items_expired > 0 ? "var(--red-expired)" : "var(--green-fresh)"}
          />
        </div>
      </div>

      {/* Violations */}
      {reward.violations && reward.violations.length > 0 && (
        <div style={{ marginTop: 20, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.7rem",
              color: "var(--red-expired)",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              marginBottom: 8,
            }}
          >
            Violations ({reward.violations.length})
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {reward.violations.slice(0, 10).map((v, i) => (
              <div
                key={i}
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.75rem",
                  color: "var(--text-secondary)",
                  padding: "4px 8px",
                  background: "rgba(239, 68, 68, 0.05)",
                  borderRadius: 4,
                  borderLeft: "2px solid var(--red-expired)",
                }}
              >
                {v}
              </div>
            ))}
            {reward.violations.length > 10 && (
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "var(--text-muted)" }}>
                ...and {reward.violations.length - 10} more
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, color }) {
  return (
    <div>
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "0.65rem",
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "1.5rem",
          fontWeight: 400,
          color,
        }}
      >
        {value}
      </div>
    </div>
  );
}

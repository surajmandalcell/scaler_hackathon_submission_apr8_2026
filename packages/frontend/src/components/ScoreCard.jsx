export default function ScoreCard({ reward }) {
  if (!reward) return null;

  const pct = Math.round(reward.score * 100);
  const scoreColor = reward.score >= 0.8 ? "var(--ok)" : reward.score >= 0.5 ? "var(--warn)" : "var(--danger)";

  return (
    <section className="enter" style={{
      background: "var(--bg-raised)", border: "1px solid var(--line)",
      borderRadius: "var(--r-lg)", padding: "36px",
    }}>
      {/* Score + metrics row */}
      <div style={{ display: "flex", gap: 40, alignItems: "flex-start" }}>

        {/* Big score */}
        <div style={{ animation: "reveal 0.5s ease-out both" }}>
          <div style={{
            fontFamily: "var(--serif)", fontSize: "3.5rem", fontWeight: 300,
            color: scoreColor, lineHeight: 1, letterSpacing: "-0.03em",
          }}>
            {pct}
          </div>
          <div style={{
            fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--t4)",
            textTransform: "uppercase", letterSpacing: "0.08em", marginTop: 4,
          }}>
            Grader Score
          </div>
        </div>

        {/* Metrics */}
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 24,
          flex: 1, paddingTop: 4,
        }}>
          <Metric label="Waste" value={`${Math.round(reward.waste_rate * 100)}%`}
            tone={reward.waste_rate > 0.3 ? "danger" : "ok"} />
          <Metric label="Nutrition" value={`${Math.round(reward.nutrition_score * 100)}%`}
            tone={reward.nutrition_score > 0.5 ? "ok" : "warn"} />
          <Metric label="Used" value={reward.items_used} />
          <Metric label="Expired" value={reward.items_expired}
            tone={reward.items_expired > 0 ? "danger" : "ok"} />
        </div>
      </div>

      {/* Violations */}
      {reward.violations?.length > 0 && (
        <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid var(--line)" }}>
          <div style={{
            fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--danger)",
            textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8,
          }}>
            {reward.violations.length} violation{reward.violations.length > 1 ? "s" : ""}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
            {reward.violations.slice(0, 8).map((v, i) => (
              <div key={i} style={{
                fontFamily: "var(--mono)", fontSize: "0.73rem", color: "var(--t3)",
                paddingLeft: 10, borderLeft: "2px solid var(--danger)",
              }}>
                {v}
              </div>
            ))}
            {reward.violations.length > 8 && (
              <span style={{ fontFamily: "var(--mono)", fontSize: "0.68rem", color: "var(--t4)" }}>
                +{reward.violations.length - 8} more
              </span>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function Metric({ label, value, tone }) {
  const color = tone === "danger" ? "var(--danger)" : tone === "ok" ? "var(--ok)" : tone === "warn" ? "var(--warn)" : "var(--t1)";
  return (
    <div>
      <div style={{
        fontFamily: "var(--mono)", fontSize: "0.62rem", color: "var(--t4)",
        textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 2,
      }}>
        {label}
      </div>
      <div style={{ fontFamily: "var(--serif)", fontSize: "1.4rem", fontWeight: 300, color }}>
        {value}
      </div>
    </div>
  );
}

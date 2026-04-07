function rewardTone(reward) {
  if (reward >= 0.9) return { fg: "var(--md-on-primary-container)", bg: "var(--md-primary-container)", label: "Excellent" };
  if (reward >= 0.7) return { fg: "var(--md-on-secondary-container)", bg: "var(--md-secondary-container)", label: "Strong" };
  if (reward >= 0.5) return { fg: "var(--md-on-warning-container)", bg: "var(--md-warning-container)", label: "Partial" };
  return { fg: "var(--md-on-error-container)", bg: "var(--md-error-container)", label: "Weak" };
}

export default function ScoreCard({ result }) {
  if (!result) return null;

  const reward = result.reward ?? 0;
  const tone = rewardTone(reward);
  const bridgeReward = result.bridge_reward;
  const metricsReward = result.metrics_reward;
  const bridgeScore = result.bridge_score;
  const metricsScore = result.metrics_score;

  return (
    <div
      className="md-card md-row-reveal"
      style={{
        background: tone.bg,
        color: tone.fg,
      }}
    >
      <div className="md-stack">
        <div className="md-row-spread">
          <span
            className="md-label-large"
            style={{ color: tone.fg, opacity: 0.85, letterSpacing: "0.06em", textTransform: "uppercase" }}
          >
            Grading result
          </span>
          <span
            className="md-badge"
            style={{ background: tone.fg, color: tone.bg, opacity: 0.95 }}
          >
            {tone.label}
          </span>
        </div>

        <div className="md-stack-sm" style={{ alignItems: "center", textAlign: "center" }}>
          <span
            className="md-display-large"
            style={{
              color: tone.fg,
              fontWeight: 400,
              fontSize: "clamp(3rem, 9vw, 5.5rem)",
              lineHeight: 1,
            }}
          >
            {reward.toFixed(3)}
          </span>
          <span
            className="md-label-large"
            style={{ color: tone.fg, opacity: 0.7, letterSpacing: "0.04em" }}
          >
            of 1.000 total reward
          </span>
        </div>

        <div
          className="md-divider"
          style={{ background: tone.fg, opacity: 0.2 }}
        />

        <div className="md-row" style={{ gap: "var(--md-space-7)" }}>
          {bridgeReward !== undefined && (
            <div className="md-metric">
              <span
                className="md-metric-label"
                style={{ color: tone.fg, opacity: 0.75 }}
              >
                Bridge
              </span>
              <span
                className="md-metric-value"
                style={{ color: tone.fg }}
              >
                {bridgeReward.toFixed(3)}
              </span>
              {bridgeScore !== undefined && (
                <span
                  className="md-body-small md-mono"
                  style={{ color: tone.fg, opacity: 0.7 }}
                >
                  {bridgeScore} items
                </span>
              )}
            </div>
          )}
          {metricsReward !== undefined && (
            <div className="md-metric">
              <span
                className="md-metric-label"
                style={{ color: tone.fg, opacity: 0.75 }}
              >
                Metrics
              </span>
              <span
                className="md-metric-value"
                style={{ color: tone.fg }}
              >
                {metricsReward.toFixed(3)}
              </span>
              {metricsScore !== undefined && (
                <span
                  className="md-body-small md-mono"
                  style={{ color: tone.fg, opacity: 0.7 }}
                >
                  {metricsScore}
                </span>
              )}
            </div>
          )}
        </div>

        {result.correct_nav_bridge && (
          <details>
            <summary
              className="md-label-large"
              style={{
                color: tone.fg,
                opacity: 0.85,
                cursor: "pointer",
                userSelect: "none",
                marginTop: "var(--md-space-2)",
              }}
            >
              Show correct answer
            </summary>
            <pre
              style={{
                marginTop: "var(--md-space-3)",
                background: "rgba(255,255,255,0.5)",
                color: "var(--md-on-surface)",
                maxHeight: 320,
                overflow: "auto",
              }}
            >
              {JSON.stringify(result.correct_nav_bridge, null, 2)}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}

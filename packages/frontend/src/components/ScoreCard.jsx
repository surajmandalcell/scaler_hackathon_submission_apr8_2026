function rewardClass(reward) {
  if (reward >= 0.9) return "positive";
  if (reward >= 0.7) return "accent-blue";
  if (reward >= 0.5) return "warn";
  return "negative";
}

export default function ScoreCard({ result }) {
  if (!result) return null;

  const reward = result.reward ?? 0;
  const bridgeReward = result.bridge_reward;
  const metricsReward = result.metrics_reward;
  const bridgeScore = result.bridge_score;
  const metricsScore = result.metrics_score;

  return (
    <div className="card card-accent-emerald fade-in">
      <div className="section-header">
        <p className="eyebrow mono">Grading result</p>
        <h3 className="serif">Agent Score</h3>
      </div>
      <div className="score-display">
        <p className={`score-huge serif ${rewardClass(reward)}`}>{reward.toFixed(3)}</p>
        <p className="metric-label">of 1.000 total reward</p>
      </div>
      <div className="divider"></div>
      <div className="row">
        {bridgeReward !== undefined && (
          <div>
            <p className="metric-label">Bridge Score</p>
            <p className="metric-number">{bridgeReward.toFixed(3)}</p>
            {bridgeScore !== undefined && (
              <p className="muted small mono">{bridgeScore} items correct</p>
            )}
          </div>
        )}
        {metricsReward !== undefined && (
          <div>
            <p className="metric-label">Metrics Score</p>
            <p className="metric-number">{metricsReward.toFixed(3)}</p>
            {metricsScore !== undefined && (
              <p className="muted small mono">{metricsScore} correct</p>
            )}
          </div>
        )}
      </div>
      {result.correct_nav_bridge && (
        <>
          <div className="divider"></div>
          <details>
            <summary className="metric-label clickable">Show correct answer</summary>
            <pre className="mono small correct-answer">
              {JSON.stringify(result.correct_nav_bridge, null, 2)}
            </pre>
          </details>
        </>
      )}
    </div>
  );
}

import { useState } from "react";
import ScoreCard from "../ScoreCard.jsx";

const DIFFICULTIES = [
  { id: "easy",   label: "Easy" },
  { id: "medium", label: "Medium" },
  { id: "hard",   label: "Hard" },
];

// Grading tolerances sourced from grader.py. Kept in sync so the ✔/✘ in this
// view matches what the backend grader would say for the same numbers.
const TOLERANCES = {
  bridge: 0.5,     // USD $M
  moic:   0.02,
  irr:    0.01,
  pct:    0.02,
};

function isBridgeMatch(ai, correct) {
  if (ai == null || correct == null) return false;
  return Math.abs(Number(ai) - Number(correct)) <= TOLERANCES.bridge;
}

function isMetricMatch(name, ai, correct) {
  if (ai == null || correct == null) return false;
  const tol = name === "irr" ? TOLERANCES.irr : TOLERANCES.moic;
  return Math.abs(Number(ai) - Number(correct)) <= tol;
}

function fmt(v) {
  if (v == null || v === "") return "—";
  if (typeof v === "number") return v.toFixed(4);
  return String(v);
}

export default function TestRun({ taskId, setTaskId }) {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleRun() {
    setRunning(true);
    setResult(null);
    setError(null);
    try {
      const resp = await fetch(`/api/admin/test-run?task_id=${taskId}`, {
        method: "POST",
      });
      if (!resp.ok) throw new Error(`test-run ${resp.status}`);
      const body = await resp.json();
      setResult(body);
    } catch (err) {
      setError(err.message || "test-run failed");
    } finally {
      setRunning(false);
    }
  }

  // Build a comparison table for the primary fund the baseline submitted
  function buildComparison() {
    if (!result || !result.run || !result.correct_answers) return null;
    const run = result.run;
    const primaryFund = run.primary_fund;
    const correctEntry = result.correct_answers[primaryFund] || {};

    // The baseline's submitted bridge is in the last step's args, but the
    // tool result from step 2 (get_nav_bridge) is the structured dict we want.
    const bridgeStep = (run.steps || []).find((s) => s.action === "get_nav_bridge");
    const aiBridge = bridgeStep?.result || {};
    const correctBridge = correctEntry.nav_bridge || {};

    const bridgeRows = Object.keys(correctBridge).map((k) => ({
      key: k,
      ai: aiBridge[k],
      correct: correctBridge[k],
      pass: isBridgeMatch(aiBridge[k], correctBridge[k]),
    }));

    // Metrics only present on medium/hard
    const metricsStep = (run.steps || []).find((s) => s.action === "get_portfolio_summary");
    const aiMetrics = metricsStep?.result || {};
    const correctMetrics = correctEntry.metrics || {};
    const metricKeys = [];
    if (taskId === "medium") metricKeys.push("moic");
    if (taskId === "hard") metricKeys.push("moic", "irr");
    const metricRows = metricKeys.map((k) => ({
      key: k,
      ai: aiMetrics[k],
      correct: correctMetrics[k],
      pass: isMetricMatch(k, aiMetrics[k], correctMetrics[k]),
    }));

    return { primaryFund, fundName: correctEntry.fund_name, bridgeRows, metricRows };
  }

  const comparison = buildComparison();

  return (
    <div className="md-stack-lg">
      <section className="md-card">
        <div className="md-stack">
          <div className="md-stack-sm">
            <span className="md-label-large md-on-surface-variant">Difficulty</span>
            <div className="md-row" role="group" aria-label="Difficulty">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  className={`md-chip ${taskId === d.id ? "is-selected" : ""}`}
                  onClick={() => {
                    setTaskId(d.id);
                    setResult(null);
                    setError(null);
                  }}
                  aria-pressed={taskId === d.id}
                  disabled={running}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>
          <div className="md-row">
            <button
              type="button"
              className="md-btn md-btn-filled md-btn-lg"
              onClick={handleRun}
              disabled={running}
            >
              {running ? "Running…" : "Run baseline agent"}
            </button>
            <span className="md-body-medium md-on-surface-variant">
              Task: <strong className="md-on-surface">{taskId}</strong>
            </span>
          </div>
        </div>
      </section>

      {error && (
        <div className="md-card" style={{ background: "var(--md-error-container)" }}>
          <p style={{ color: "var(--md-on-error-container)" }}>{error}</p>
        </div>
      )}

      {comparison && (
        <section className="md-stack-lg">
          <div className="md-stack-sm">
            <span className="md-eyebrow">Side-by-side</span>
            <h3 className="md-headline-small">
              AI vs Correct — {comparison.fundName || comparison.primaryFund}
            </h3>
          </div>

          <div className="md-table-wrap">
            <table className="md-table">
              <thead>
                <tr>
                  <th>Line item</th>
                  <th style={{ textAlign: "right" }}>AI's answer</th>
                  <th style={{ textAlign: "right" }}>Correct</th>
                  <th style={{ textAlign: "center" }}>Match</th>
                </tr>
              </thead>
              <tbody>
                {comparison.bridgeRows.map((r) => (
                  <tr key={r.key}>
                    <td>{r.key}</td>
                    <td className="md-mono" style={{ textAlign: "right" }}>{fmt(r.ai)}</td>
                    <td className="md-mono" style={{ textAlign: "right" }}>{fmt(r.correct)}</td>
                    <td style={{ textAlign: "center" }} className={r.pass ? "md-pos" : "md-neg"}>
                      {r.pass ? "✔" : "✘"}
                    </td>
                  </tr>
                ))}
                {comparison.metricRows.map((r) => (
                  <tr key={`m-${r.key}`}>
                    <td><em>{r.key}</em></td>
                    <td className="md-mono" style={{ textAlign: "right" }}>{fmt(r.ai)}</td>
                    <td className="md-mono" style={{ textAlign: "right" }}>{fmt(r.correct)}</td>
                    <td style={{ textAlign: "center" }} className={r.pass ? "md-pos" : "md-neg"}>
                      {r.pass ? "✔" : "✘"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {result?.run?.grading && <ScoreCard result={result.run.grading} />}
        </section>
      )}
    </div>
  );
}

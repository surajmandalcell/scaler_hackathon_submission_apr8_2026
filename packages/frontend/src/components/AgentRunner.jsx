import { useState } from "react";
import ScoreCard from "./ScoreCard.jsx";
import { summarizeArgs, summarizeResult } from "../utils/summarize.js";

const DIFFICULTIES = [
  { id: "easy",   label: "Easy" },
  { id: "medium", label: "Medium" },
  { id: "hard",   label: "Hard" },
];

const ACTION_LABELS = {
  reset:                "Reset episode",
  get_nav_bridge:       "get_nav_bridge",
  get_portfolio_summary:"get_portfolio_summary",
  submit_report:        "submit_report",
};

export default function AgentRunner({ taskId, setTaskId }) {
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState([]);
  const [grading, setGrading] = useState(null);
  const [error, setError] = useState(null);

  async function runBaseline() {
    setRunning(true);
    setSteps([]);
    setGrading(null);
    setError(null);

    try {
      const resp = await fetch(`/api/run-agent?task_id=${taskId}`, {
        method: "POST",
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`run-agent ${resp.status}: ${text.slice(0, 120)}`);
      }
      const data = await resp.json();
      if (data.error) {
        setError(data.error);
        if (Array.isArray(data.steps)) setSteps(data.steps);
        return;
      }
      setSteps(data.steps || []);
      setGrading(data.grading || null);
    } catch (err) {
      console.error("Agent run failed:", err);
      setError(err.message || "Agent run failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="md-stack-lg md-reveal">
      {/* ── Hero ── */}
      <section className="md-stack-sm">
        <span className="md-eyebrow">04 — Evaluation</span>
        <h2 className="md-section-title">Agent Runner</h2>
        <p className="md-body-large md-on-surface-variant" style={{ maxWidth: 680 }}>
          Runs the baseline pass-through agent against the live environment.
          The agent calls <code>get_nav_bridge</code>, optionally{" "}
          <code>get_portfolio_summary</code> for metrics, then submits via{" "}
          <code>submit_report</code> for grading.
        </p>
      </section>

      {/* ── Controls ── */}
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
                    setSteps([]);
                    setGrading(null);
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
              onClick={runBaseline}
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

      {/* ── Error ── */}
      {error && (
        <div className="md-card" style={{ background: "var(--md-error-container)" }}>
          <div className="md-stack-sm">
            <span
              className="md-label-large"
              style={{ color: "var(--md-on-error-container)" }}
            >
              Run failed
            </span>
            <p style={{ color: "var(--md-on-error-container)" }}>{error}</p>
          </div>
        </div>
      )}

      {/* ── Step log ── */}
      {steps.length > 0 && (
        <section className="md-stack">
          <div className="md-stack-sm">
            <span className="md-eyebrow">Execution log</span>
            <h3 className="md-headline-small">
              {steps.length} {steps.length === 1 ? "step" : "steps"}
            </h3>
          </div>

          <ol className="md-stack" style={{ listStyle: "none", padding: 0 }}>
            {steps.map((step) => (
              <li key={step.n} className="md-card md-card-tonal-secondary md-row-reveal">
                <div className="md-stack-sm">
                  <div className="md-row-spread">
                    <div className="md-row" style={{ gap: "var(--md-space-3)" }}>
                      <span className="md-badge md-badge-primary">
                        Step {String(step.n).padStart(2, "0")}
                      </span>
                      <code>{ACTION_LABELS[step.action] || step.action}</code>
                    </div>
                  </div>
                  {summarizeArgs(step.args) && (
                    <p
                      className="md-body-small md-mono"
                      style={{ color: "var(--md-on-secondary-container)" }}
                    >
                      args · {summarizeArgs(step.args)}
                    </p>
                  )}
                  {summarizeResult(step.result) && (
                    <p
                      className="md-body-small md-mono"
                      style={{ color: "var(--md-on-secondary-container)" }}
                    >
                      result · {summarizeResult(step.result)}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {/* ── Final score ── */}
      {grading && <ScoreCard result={grading} />}
    </div>
  );
}

import { useState } from "react";
import ScoreCard from "./ScoreCard.jsx";

async function callStep(toolName, args = {}) {
  const resp = await fetch("/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool_name: toolName, arguments: args }),
  });
  return resp.json();
}

async function callReset(taskId) {
  const resp = await fetch("/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_id: taskId }),
  });
  return resp.json();
}

function summarizeResult(result) {
  if (!result) return "no data";
  if (typeof result !== "object") return String(result);
  const keys = Object.keys(result);
  if (keys.length === 0) return "{}";
  const preview = keys.slice(0, 4).map((k) => {
    const v = result[k];
    if (typeof v === "number") return `${k}: ${v}`;
    if (typeof v === "string") return `${k}: "${v.slice(0, 30)}"`;
    return `${k}: ...`;
  }).join(", ");
  return keys.length > 4 ? `${preview}, +${keys.length - 4} more` : preview;
}

export default function AgentRunner({ taskId, scenario, onResult }) {
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState([]);
  const [finalResult, setFinalResult] = useState(null);
  const [error, setError] = useState(null);

  async function runBaseline() {
    setRunning(true);
    setSteps([]);
    setFinalResult(null);
    setError(null);

    try {
      // Step 1: Reset
      const resetObs = await callReset(taskId);
      const observation = resetObs.observation || resetObs;
      const funds = observation.available_funds || [];
      if (funds.length === 0) throw new Error("No funds available after reset");

      setSteps((prev) => [...prev, {
        n: 1,
        action: "reset",
        args: { task_id: taskId },
        result: { available_funds: funds, task: observation.difficulty || taskId },
      }]);

      // Step 2: Get NAV bridge for first fund
      const primaryFund = funds[0];
      const bridgeObs = await callStep("get_nav_bridge", { fund_id: primaryFund });
      const bridge = bridgeObs.observation?.tool_result || bridgeObs.tool_result || bridgeObs;

      setSteps((prev) => [...prev, {
        n: 2,
        action: "get_nav_bridge",
        args: { fund_id: primaryFund },
        result: bridge,
      }]);

      if (bridge.error) throw new Error(bridge.error);

      // Step 3: Optionally get metrics for medium/hard
      let metrics = null;
      if (taskId === "medium" || taskId === "hard") {
        const metricsObs = await callStep("get_portfolio_summary", { funds: [primaryFund] });
        const metricsData = metricsObs.observation?.tool_result || metricsObs.tool_result || {};
        const fundMetrics = metricsData[primaryFund] || {};
        metrics = {};
        if (taskId === "medium") metrics.moic = fundMetrics.moic;
        if (taskId === "hard") {
          metrics.moic = fundMetrics.moic;
          metrics.irr = fundMetrics.irr;
        }

        setSteps((prev) => [...prev, {
          n: 3,
          action: "get_portfolio_summary",
          args: { funds: [primaryFund] },
          result: fundMetrics,
        }]);
      }

      // Step 4: Submit report
      const submitArgs = { nav_bridge: bridge };
      if (metrics) submitArgs.metrics = metrics;

      const submitObs = await callStep("submit_report", submitArgs);
      const grading = submitObs.observation?.tool_result || submitObs.tool_result || submitObs;

      setSteps((prev) => [...prev, {
        n: prev.length + 1,
        action: "submit_report",
        args: metrics ? { bridge: "8 items", metrics: Object.keys(metrics).join(", ") } : { bridge: "8 items" },
        result: grading,
      }]);

      setFinalResult(grading);
      if (onResult) onResult(grading);
    } catch (err) {
      setError(err.message || "Agent run failed");
      console.error(err);
    } finally {
      setRunning(false);
    }
  }

  if (!scenario) {
    return (
      <div className="stack">
        <div className="section-header">
          <p className="eyebrow mono">04 -- Evaluation</p>
          <h2 className="serif section-title">Agent Runner</h2>
        </div>
        <div className="empty-state">
          <p className="serif muted">Load a scenario from the Dashboard before running an agent.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stack">
      <div className="section-header">
        <p className="eyebrow mono">04 -- Evaluation</p>
        <h2 className="serif section-title">Agent Runner</h2>
      </div>

      <div className="card card-accent-blue">
        <p className="metric-label">Baseline strategy</p>
        <p className="muted small">
          The baseline calls <code className="mono">get_nav_bridge</code> for the primary fund,
          {taskId !== "easy" && <> then <code className="mono">get_portfolio_summary</code> for MOIC{taskId === "hard" && "/IRR"},</>}
          {" "}then submits the result via <code className="mono">submit_report</code>. This demonstrates a pass-through agent -- no reasoning.
        </p>
      </div>

      <div className="row controls-row">
        <button
          type="button"
          className="btn-primary"
          onClick={runBaseline}
          disabled={running}
        >
          {running ? "Running..." : "Run Baseline Agent"}
        </button>
        <p className="mono small muted">Current task: {taskId}</p>
      </div>

      {error && (
        <div className="card card-accent-red">
          <p className="metric-label">Error</p>
          <p className="mono small">{error}</p>
        </div>
      )}

      {steps.length > 0 && (
        <div className="stack">
          <div className="section-header">
            <p className="eyebrow mono">Execution log</p>
          </div>
          <div className="stack step-log">
            {steps.map((step) => (
              <div key={step.n} className="card step-card fade-in">
                <div className="row step-header">
                  <span className="step-number mono">{String(step.n).padStart(2, "0")}</span>
                  <span className="step-action mono">{step.action}</span>
                </div>
                <p className="muted small mono">args: {summarizeResult(step.args)}</p>
                <div className="divider"></div>
                <p className="muted small mono">result: {summarizeResult(step.result)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {finalResult && <ScoreCard result={finalResult} />}
    </div>
  );
}

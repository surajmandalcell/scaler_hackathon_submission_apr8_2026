import { useCallback, useEffect, useMemo, useState } from "react";
import ToolList from "./playground/ToolList.jsx";
import ToolForm from "./playground/ToolForm.jsx";
import CallHistory from "./playground/CallHistory.jsx";

const DIFFICULTIES = [
  { id: "easy",   label: "Easy" },
  { id: "medium", label: "Medium" },
  { id: "hard",   label: "Hard" },
];

async function getJson(url) {
  const resp = await fetch(url);
  return resp.json();
}

async function postJson(url, body) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  return resp.json();
}

export default function Playground() {
  const [difficulty, setDifficulty] = useState("easy");
  const [state, setState] = useState(null);
  const [tools, setTools] = useState([]);
  const [selectedName, setSelectedName] = useState(null);
  const [history, setHistory] = useState([]);
  const [running, setRunning] = useState(false);
  const [presetArgs, setPresetArgs] = useState(null);
  const [initError, setInitError] = useState(null);

  // Load tool catalogue and session state on mount.
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [toolsResp, stateResp] = await Promise.all([
          getJson("/api/session/tools"),
          getJson("/api/session/state"),
        ]);
        if (!alive) return;
        setTools(toolsResp.tools || []);
        setState(stateResp);
        // Default to the submit_report tool so newcomers see the goal
        setSelectedName((prev) => prev || (toolsResp.tools?.[0]?.name ?? null));
      } catch (err) {
        setInitError(err.message);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const refreshState = useCallback(async () => {
    try {
      const s = await getJson("/api/session/state");
      setState(s);
    } catch (err) {
      console.error("Refresh state failed:", err);
    }
  }, []);

  async function handleReset() {
    setRunning(true);
    try {
      const body = await postJson("/api/session/reset", { task_id: difficulty });
      setState(body.state);
      setHistory([]);
    } finally {
      setRunning(false);
    }
  }

  async function handleCall(toolName, args) {
    setRunning(true);
    try {
      const body = await postJson("/api/session/step", {
        tool_name: toolName,
        arguments: args,
      });
      setHistory((prev) => [
        ...prev,
        {
          n: prev.length + 1,
          tool_name: body.tool_name,
          arguments: body.arguments,
          result: body.result,
          ts: Date.now(),
        },
      ]);
      if (body.state) setState(body.state);
      setPresetArgs(null);
    } finally {
      setRunning(false);
    }
  }

  // Build `submit_report` payload from the most recent get_nav_bridge and
  // get_portfolio_summary results in history, and seed ToolForm with it.
  function handlePrefillSubmit() {
    const lastBridge = [...history].reverse().find((h) => h.tool_name === "get_nav_bridge");
    const lastMetrics = [...history]
      .reverse()
      .find((h) => h.tool_name === "get_portfolio_summary");
    if (!lastBridge) {
      alert("Call get_nav_bridge at least once first.");
      return;
    }
    const preset = { nav_bridge: lastBridge.result };
    if (lastMetrics && lastMetrics.result && typeof lastMetrics.result === "object") {
      const first = Object.values(lastMetrics.result)[0];
      if (first) {
        const metrics = {};
        if ("moic" in first) metrics.moic = first.moic;
        if ("irr" in first) metrics.irr = first.irr;
        if (Object.keys(metrics).length > 0) preset.metrics = metrics;
      }
    }
    setSelectedName("submit_report");
    setPresetArgs(preset);
  }

  function handleClearHistory() {
    setHistory([]);
  }

  function handleUseResult(entry) {
    // Clicking "Use ↗" on a history entry with get_available_filters doesn't
    // preset any tool; it's mostly useful for bridge/metrics results that you
    // want to reuse as inputs to the next call.
    if (entry.tool_name === "get_nav_bridge") {
      // Preset could be used by a future tool, but the common case is
      // feeding it into submit_report — delegate to handlePrefillSubmit.
      handlePrefillSubmit();
    }
  }

  const selectedTool = useMemo(
    () => tools.find((t) => t.name === selectedName) || null,
    [tools, selectedName]
  );

  const availableFunds = state?.funds_loaded || [];
  const availableDeals = state?.deals_loaded || [];

  return (
    <div className="md-stack-lg md-reveal">
      <section className="md-stack-sm">
        <span className="md-eyebrow">Agent tooling</span>
        <h2 className="md-section-title">MCP Playground</h2>
        <p className="md-body-large md-on-surface-variant" style={{ maxWidth: 680 }}>
          Drive the same MCP tool surface an AI agent uses, by hand. Reset a
          session, call any of the {tools.length || 15}+ tools one at a time,
          inspect every JSON response, and submit a report to see how it
          grades. The session is shared with <code>/api/run-agent</code> —
          everything runs against the same in-process environment.
        </p>
      </section>

      {initError && (
        <div className="md-card" style={{ background: "var(--md-error-container)" }}>
          <p style={{ color: "var(--md-on-error-container)" }}>{initError}</p>
        </div>
      )}

      {/* ── Session header ─────────────────────────────────────────────── */}
      <section className="md-card">
        <div className="md-stack">
          <div className="md-stack-sm">
            <span className="md-label-large md-on-surface-variant">Session</span>
            <div className="md-row" role="group" aria-label="Difficulty">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  className={`md-chip ${difficulty === d.id ? "is-selected" : ""}`}
                  onClick={() => setDifficulty(d.id)}
                  aria-pressed={difficulty === d.id}
                  disabled={running}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          <div className="md-row" style={{ alignItems: "center" }}>
            <button
              type="button"
              className="md-btn md-btn-filled"
              onClick={handleReset}
              disabled={running}
            >
              {running ? "Working…" : "Reset session"}
            </button>
            <button
              type="button"
              className="md-btn md-btn-tonal"
              onClick={handlePrefillSubmit}
              disabled={running || history.length === 0}
              title="Pre-fill the submit_report form from your last bridge + metrics calls"
            >
              Prep submit_report
            </button>
            <button
              type="button"
              className="md-btn md-btn-text md-btn-sm"
              onClick={refreshState}
            >
              Refresh state
            </button>
          </div>

          {state && (
            <div className="md-grid" style={{ gridTemplateColumns: "repeat(3, 1fr)", gap: "var(--md-space-4)" }}>
              <div className="md-metric">
                <span className="md-metric-label">task_id</span>
                <span className="md-metric-value-sm md-mono">
                  {state.task_id || "—"}
                </span>
              </div>
              <div className="md-metric">
                <span className="md-metric-label">funds loaded</span>
                <span className="md-metric-value-sm md-mono">
                  {availableFunds.length}
                </span>
              </div>
              <div className="md-metric">
                <span className="md-metric-label">calls this session</span>
                <span className="md-metric-value-sm md-mono">
                  {history.length}
                </span>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ── Split pane: tools | form + history ────────────────────────── */}
      <div className="pg-shell">
        <aside className="pg-tools">
          <div className="md-stack-sm">
            <span className="md-eyebrow">Tools ({tools.length})</span>
            <p className="md-body-small md-on-surface-variant">
              All MCP tools the agent can call.
            </p>
          </div>
          <ToolList tools={tools} selectedName={selectedName} onSelect={setSelectedName} />
        </aside>

        <div className="pg-work md-stack-lg">
          <ToolForm
            tool={selectedTool}
            availableFunds={availableFunds}
            availableDeals={availableDeals}
            presetArgs={presetArgs}
            onCall={handleCall}
            running={running}
          />
          <CallHistory entries={history} onClear={handleClearHistory} onUseResult={handleUseResult} />
        </div>
      </div>
    </div>
  );
}

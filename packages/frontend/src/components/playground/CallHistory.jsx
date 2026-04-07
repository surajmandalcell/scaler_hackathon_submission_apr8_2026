import { summarizeArgs, summarizeResult } from "../../utils/summarize.js";

// Right pane bottom: append-only log of every call made this session. Each
// entry is a tonal card; click the "expand" button to see the full JSON
// response. The log is purely client-side state — "Clear history" only wipes
// the local array, it doesn't reset the backend session.

export default function CallHistory({ entries, onClear, onUseResult }) {
  if (!entries || entries.length === 0) {
    return (
      <div className="md-empty">
        <p className="md-empty-title">No calls yet</p>
        <p className="md-empty-text">
          Pick a tool, fill in its arguments, and click <em>Call tool</em> to
          start a log.
        </p>
      </div>
    );
  }

  return (
    <div className="md-stack">
      <div className="md-row-spread">
        <span className="md-eyebrow">
          {entries.length} {entries.length === 1 ? "call" : "calls"} this session
        </span>
        <button type="button" className="md-btn md-btn-text md-btn-sm" onClick={onClear}>
          Clear history
        </button>
      </div>

      {entries.map((entry) => (
        <article key={entry.n} className="md-card md-card-tonal-secondary">
          <div className="md-stack-sm">
            <div className="md-row-spread">
              <div className="md-row" style={{ gap: "var(--md-space-3)" }}>
                <span className="md-badge md-badge-primary">
                  Step {String(entry.n).padStart(2, "0")}
                </span>
                <code className="md-title-small">{entry.tool_name}</code>
              </div>
              {onUseResult && (
                <button
                  type="button"
                  className="md-btn md-btn-text md-btn-sm"
                  onClick={() => onUseResult(entry)}
                  title="Reuse this result when building a submit_report payload"
                >
                  Use ↗
                </button>
              )}
            </div>
            {summarizeArgs(entry.arguments) && (
              <p
                className="md-body-small md-mono"
                style={{ color: "var(--md-on-secondary-container)" }}
              >
                args · {summarizeArgs(entry.arguments)}
              </p>
            )}
            {summarizeResult(entry.result) && (
              <p
                className="md-body-small md-mono"
                style={{ color: "var(--md-on-secondary-container)" }}
              >
                result · {summarizeResult(entry.result)}
              </p>
            )}
            <details>
              <summary className="md-body-small md-on-surface-variant" style={{ cursor: "pointer" }}>
                Full JSON
              </summary>
              <pre
                className="md-mono md-body-small"
                style={{
                  background: "var(--md-surface-container-lowest)",
                  padding: "var(--md-space-3)",
                  borderRadius: "var(--md-shape-sm)",
                  overflow: "auto",
                  marginTop: "var(--md-space-2)",
                  maxHeight: 320,
                }}
              >
                {JSON.stringify(entry.result, null, 2)}
              </pre>
            </details>
          </div>
        </article>
      ))}
    </div>
  );
}

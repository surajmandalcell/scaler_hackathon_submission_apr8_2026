// Left pane: the full catalogue of MCP tools the agent has access to. Each
// card is an `md-card-interactive`; click to select.

export default function ToolList({ tools, selectedName, onSelect }) {
  if (!tools || tools.length === 0) {
    return (
      <div className="md-empty">
        <p className="md-empty-title">Loading tools…</p>
        <p className="md-empty-text">
          Tool catalogue is fetched from <code>/api/session/tools</code>.
        </p>
      </div>
    );
  }

  return (
    <div className="md-stack">
      {tools.map((tool) => {
        const isActive = tool.name === selectedName;
        const argNames = Object.keys(tool.parameters?.properties || {});
        const firstLine = (tool.description || "").split("\n")[0];
        return (
          <button
            key={tool.name}
            type="button"
            className={`md-card md-card-interactive ${isActive ? "is-active" : ""}`}
            onClick={() => onSelect(tool.name)}
            style={{
              textAlign: "left",
              border: isActive
                ? "2px solid var(--md-primary)"
                : "1px solid var(--md-outline-variant)",
            }}
          >
            <div className="md-stack-sm">
              <span className="md-title-small md-mono">{tool.name}</span>
              {firstLine && (
                <span className="md-body-small md-on-surface-variant">
                  {firstLine.length > 110 ? firstLine.slice(0, 107) + "…" : firstLine}
                </span>
              )}
              {argNames.length > 0 && (
                <div className="md-row" style={{ flexWrap: "wrap", gap: "var(--md-space-2)" }}>
                  {argNames.map((arg) => (
                    <span key={arg} className="md-badge md-badge-tertiary">
                      {arg}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}

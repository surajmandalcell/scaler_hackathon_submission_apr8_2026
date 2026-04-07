import { useEffect, useMemo, useState } from "react";

// Right pane top: dynamically render inputs for the selected MCP tool based
// on its JSON Schema parameters. Coerce values to the right JS types on
// submit so the backend receives real numbers/arrays instead of strings.

const FUND_LIKE_NAMES = new Set(["fund_id", "funds"]);
const DEAL_LIKE_NAMES = new Set(["deal_id", "deals"]);

function coerce(value, schema) {
  if (value === "" || value == null) return undefined;
  const type = schema?.type;
  const itemType = schema?.items?.type;

  if (type === "number" || type === "integer") {
    const n = Number(value);
    return Number.isNaN(n) ? undefined : n;
  }
  if (type === "boolean") return value === true || value === "true";
  if (type === "array") {
    // CSV input for array fields
    const parts = String(value)
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (itemType === "number" || itemType === "integer") {
      return parts.map(Number).filter((n) => !Number.isNaN(n));
    }
    return parts;
  }
  return value;
}

function FieldInput({ name, schema, availableFunds, availableDeals, value, onChange }) {
  const type = schema?.type;
  const itemType = schema?.items?.type;

  // fund_id -> dropdown
  if (FUND_LIKE_NAMES.has(name) && type === "string") {
    return (
      <select className="md-select" value={value ?? ""} onChange={(e) => onChange(e.target.value)}>
        <option value="">— pick a fund —</option>
        {availableFunds.map((f) => (
          <option key={f} value={f}>{f}</option>
        ))}
      </select>
    );
  }
  // funds: list<string> -> multi-select via comma-separated display; for now use a simple text input
  if (FUND_LIKE_NAMES.has(name) && type === "array") {
    return (
      <input
        className="md-select"
        placeholder="alpha, beta"
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }
  // deal_id -> text input but show available deals as placeholder
  if (DEAL_LIKE_NAMES.has(name) && type === "string") {
    const first = availableDeals[0] || "";
    return (
      <input
        className="md-select"
        placeholder={first ? `e.g. ${first}` : "deal_id"}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }
  // Generic number
  if (type === "number" || type === "integer") {
    return (
      <input
        className="md-select"
        type="number"
        step={type === "integer" ? "1" : "any"}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }
  if (type === "boolean") {
    return (
      <select
        className="md-select"
        value={String(value ?? "false")}
        onChange={(e) => onChange(e.target.value === "true")}
      >
        <option value="false">false</option>
        <option value="true">true</option>
      </select>
    );
  }
  if (type === "array") {
    return (
      <input
        className="md-select"
        placeholder={itemType === "number" ? "1.0, 2.0" : "item1, item2"}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }
  if (type === "object") {
    return (
      <textarea
        className="md-select"
        rows={4}
        placeholder='{"key": "value"}'
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
      />
    );
  }
  // default: string
  return (
    <input
      className="md-select"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}

export default function ToolForm({
  tool,
  availableFunds,
  availableDeals,
  onCall,
  presetArgs,
  running,
}) {
  const [values, setValues] = useState({});

  // Reset or preload form state whenever the tool changes or a preset is pushed.
  useEffect(() => {
    if (presetArgs) {
      setValues(
        Object.fromEntries(
          Object.entries(presetArgs).map(([k, v]) => [
            k,
            typeof v === "object" ? JSON.stringify(v) : String(v),
          ])
        )
      );
    } else {
      setValues({});
    }
  }, [tool?.name, presetArgs]);

  const schema = tool?.parameters;
  const props = schema?.properties || {};
  const required = new Set(schema?.required || []);
  const argNames = Object.keys(props);

  const canSubmit = useMemo(() => {
    if (!tool) return false;
    for (const name of required) {
      const v = values[name];
      if (v == null || v === "") return false;
    }
    return true;
  }, [tool, values, required]);

  if (!tool) {
    return (
      <div className="md-empty">
        <p className="md-empty-title">Pick a tool on the left</p>
        <p className="md-empty-text">
          Every tool the agent has access to is listed — click one to see its
          inputs.
        </p>
      </div>
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const payload = {};
    for (const [name, sch] of Object.entries(props)) {
      let raw = values[name];
      if (sch.type === "object" && typeof raw === "string" && raw.trim()) {
        try {
          payload[name] = JSON.parse(raw);
          continue;
        } catch {
          alert(`Argument '${name}' must be valid JSON`);
          return;
        }
      }
      const coerced = coerce(raw, sch);
      if (coerced !== undefined) payload[name] = coerced;
    }
    onCall(tool.name, payload);
  }

  return (
    <section className="md-card">
      <div className="md-stack">
        <div className="md-stack-sm">
          <span className="md-eyebrow">Selected tool</span>
          <h3 className="md-headline-small md-mono">{tool.name}</h3>
          {tool.description && (
            <p className="md-body-medium md-on-surface-variant">
              {tool.description}
            </p>
          )}
        </div>

        <form onSubmit={handleSubmit} className="md-stack">
          {argNames.length === 0 && (
            <p className="md-body-small md-on-surface-variant">
              This tool takes no arguments.
            </p>
          )}
          {argNames.map((name) => {
            const sch = props[name];
            return (
              <label key={name} className="md-field">
                <span className="md-field-label">
                  {name}
                  {required.has(name) && <span className="md-error-text"> *</span>}
                  {sch.type && (
                    <span className="md-body-small md-on-surface-variant">
                      {"  "}({sch.type}
                      {sch.items?.type ? `<${sch.items.type}>` : ""})
                    </span>
                  )}
                </span>
                <FieldInput
                  name={name}
                  schema={sch}
                  availableFunds={availableFunds}
                  availableDeals={availableDeals}
                  value={values[name]}
                  onChange={(v) => setValues((prev) => ({ ...prev, [name]: v }))}
                />
              </label>
            );
          })}

          <div className="md-row">
            <button
              type="submit"
              className="md-btn md-btn-filled md-btn-lg"
              disabled={!canSubmit || running}
            >
              {running ? "Calling…" : "Call tool"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}

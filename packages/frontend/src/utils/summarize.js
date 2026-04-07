// Shared pretty-printers for tool arguments and results. Used by both the
// canned AgentRunner and the interactive Playground so the log formatting
// stays consistent across both surfaces.

export function summarizeArgs(args) {
  if (!args || typeof args !== "object") return "";
  const entries = Object.entries(args);
  if (entries.length === 0) return "";
  return entries
    .map(([k, v]) => {
      if (Array.isArray(v)) return `${k}: [${v.join(", ")}]`;
      if (typeof v === "object" && v !== null) return `${k}: …`;
      return `${k}: ${v}`;
    })
    .join("  ·  ");
}

export function summarizeResult(result) {
  if (!result || typeof result !== "object") return "";
  const keys = Object.keys(result);
  if (keys.length === 0) return "{}";
  const preview = keys
    .slice(0, 3)
    .map((k) => {
      const v = result[k];
      if (typeof v === "number") return `${k}: ${v}`;
      if (typeof v === "string") return `${k}: "${v.slice(0, 40)}"`;
      if (Array.isArray(v)) return `${k}: [${v.length}]`;
      return `${k}: …`;
    })
    .join("  ·  ");
  return keys.length > 3 ? `${preview}  · +${keys.length - 3}` : preview;
}

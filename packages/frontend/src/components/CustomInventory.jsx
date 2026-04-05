import { useState } from "react";

const CATEGORIES = ["protein", "carb", "vegetable", "dairy", "fruit", "condiment"];
const UNITS = ["g", "ml", "pcs"];

const EMPTY_ITEM = { name: "", category: "protein", quantity: 500, unit: "g", expiry_date: "" };

const SAMPLE_JSON = `[
  {"name": "chicken_breast", "quantity": 500, "unit": "g", "expiry_date": "2026-01-04", "category": "protein"},
  {"name": "spinach", "quantity": 200, "unit": "g", "expiry_date": "2026-01-03", "category": "vegetable"},
  {"name": "white_rice", "quantity": 1000, "unit": "g", "expiry_date": "2026-01-15", "category": "carb"}
]`;

export default function CustomInventory({ onSubmit, loading }) {
  const [mode, setMode] = useState("form");
  const [jsonText, setJsonText] = useState(SAMPLE_JSON);
  const [jsonError, setJsonError] = useState(null);
  const [items, setItems] = useState([
    { name: "chicken_breast", category: "protein", quantity: 500, unit: "g", expiry_date: "2026-01-04" },
    { name: "spinach", category: "vegetable", quantity: 200, unit: "g", expiry_date: "2026-01-03" },
    { name: "white_rice", category: "carb", quantity: 1000, unit: "g", expiry_date: "2026-01-15" },
  ]);
  const [horizon, setHorizon] = useState(7);
  const [householdSize, setHouseholdSize] = useState(2);
  const [restrictions, setRestrictions] = useState("");

  const handleAddItem = () => setItems([...items, { ...EMPTY_ITEM }]);

  const handleRemoveItem = (idx) => setItems(items.filter((_, i) => i !== idx));

  const handleItemChange = (idx, field, value) => {
    const updated = [...items];
    updated[idx] = { ...updated[idx], [field]: field === "quantity" ? Number(value) : value };
    setItems(updated);
  };

  const handleJsonSubmit = () => {
    try {
      const parsed = JSON.parse(jsonText);
      if (!Array.isArray(parsed)) throw new Error("Must be an array");
      setJsonError(null);
      onSubmit({
        inventory: parsed,
        horizon,
        household_size: householdSize,
        dietary_restrictions: restrictions ? restrictions.split(",").map((s) => s.trim()) : [],
      });
    } catch (e) {
      setJsonError(e.message);
    }
  };

  const handleFormSubmit = () => {
    const valid = items.filter((i) => i.name && i.quantity > 0 && i.expiry_date);
    if (!valid.length) return;
    onSubmit({
      inventory: valid,
      horizon,
      household_size: householdSize,
      dietary_restrictions: restrictions ? restrictions.split(",").map((s) => s.trim()) : [],
    });
  };

  const s = {
    label: { fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--t4)", textTransform: "uppercase", letterSpacing: "0.06em" },
    input: { padding: "6px 10px", borderRadius: "var(--r)", border: "1px solid var(--line)", background: "var(--bg)", color: "var(--t1)", fontFamily: "var(--mono)", fontSize: "0.8rem", outline: "none" },
    btn: { padding: "7px 16px", borderRadius: "var(--r)", border: "none", cursor: "pointer", fontFamily: "var(--sans)", fontSize: "0.8rem", fontWeight: 500 },
  };

  return (
    <section className="enter" style={{ background: "var(--bg-raised)", border: "1px solid var(--line)", borderRadius: "var(--r-lg)", padding: "32px 36px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h2 style={{ fontFamily: "var(--serif)", fontWeight: 300, fontSize: "1.25rem", color: "var(--t1)" }}>
          Custom Inventory
        </h2>
        <div style={{ display: "flex", gap: 2 }}>
          {["form", "json"].map((m) => (
            <button type="button" key={m} onClick={() => setMode(m)} style={{
              ...s.btn, background: mode === m ? "var(--accent)" : "transparent",
              color: mode === m ? "var(--bg)" : "var(--t3)", fontFamily: "var(--mono)",
            }}>
              {m === "form" ? "Form" : "JSON"}
            </button>
          ))}
        </div>
      </div>

      {/* Shared settings */}
      <div style={{ display: "flex", gap: 16, marginBottom: 20, flexWrap: "wrap" }}>
        <div>
          <div style={s.label}>Horizon (days)</div>
          <input type="number" value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} min={3} max={14} style={{ ...s.input, width: 64 }} />
        </div>
        <div>
          <div style={s.label}>Household</div>
          <input type="number" value={householdSize} onChange={(e) => setHouseholdSize(Number(e.target.value))} min={1} max={6} style={{ ...s.input, width: 64 }} />
        </div>
        <div style={{ flex: 1, minWidth: 160 }}>
          <div style={s.label}>Restrictions (comma-separated)</div>
          <input type="text" value={restrictions} onChange={(e) => setRestrictions(e.target.value)} placeholder="vegetarian, lactose-free" style={{ ...s.input, width: "100%" }} />
        </div>
      </div>

      {/* JSON Mode */}
      {mode === "json" && (
        <div>
          <textarea value={jsonText} onChange={(e) => { setJsonText(e.target.value); setJsonError(null); }}
            rows={12}
            style={{ ...s.input, width: "100%", fontFamily: "var(--mono)", fontSize: "0.75rem", resize: "vertical", lineHeight: 1.6 }}
          />
          {jsonError && <div style={{ color: "var(--danger)", fontFamily: "var(--mono)", fontSize: "0.75rem", marginTop: 6 }}>{jsonError}</div>}
          <button type="button" onClick={handleJsonSubmit} disabled={loading} style={{ ...s.btn, background: "var(--accent)", color: "var(--bg)", marginTop: 12 }}>
            {loading ? "..." : "Load Inventory"}
          </button>
        </div>
      )}

      {/* Form Mode */}
      {mode === "form" && (
        <div>
          {/* Header */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 100px 70px 60px 130px 32px", gap: 8, marginBottom: 6 }}>
            {["Name", "Category", "Qty", "Unit", "Expiry", ""].map((h) => (
              <div key={h} style={s.label}>{h}</div>
            ))}
          </div>

          {/* Rows */}
          {items.map((item, idx) => (
            <div key={idx} style={{ display: "grid", gridTemplateColumns: "1fr 100px 70px 60px 130px 32px", gap: 8, marginBottom: 4 }}>
              <input type="text" value={item.name} onChange={(e) => handleItemChange(idx, "name", e.target.value)} placeholder="item_name" style={{ ...s.input, fontSize: "0.75rem" }} />
              <select value={item.category} onChange={(e) => handleItemChange(idx, "category", e.target.value)} style={{ ...s.input, fontSize: "0.75rem" }}>
                {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
              <input type="number" value={item.quantity} onChange={(e) => handleItemChange(idx, "quantity", e.target.value)} min={1} style={{ ...s.input, fontSize: "0.75rem" }} />
              <select value={item.unit} onChange={(e) => handleItemChange(idx, "unit", e.target.value)} style={{ ...s.input, fontSize: "0.75rem" }}>
                {UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
              </select>
              <input type="date" value={item.expiry_date} onChange={(e) => handleItemChange(idx, "expiry_date", e.target.value)} style={{ ...s.input, fontSize: "0.75rem" }} />
              <button type="button" onClick={() => handleRemoveItem(idx)} style={{ ...s.btn, background: "transparent", color: "var(--danger)", padding: 0, fontSize: "1rem" }}>
                x
              </button>
            </div>
          ))}

          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button type="button" onClick={handleAddItem} style={{ ...s.btn, background: "transparent", color: "var(--t3)", border: "1px dashed var(--line)" }}>
              + Add item
            </button>
            <button type="button" onClick={handleFormSubmit} disabled={loading} style={{ ...s.btn, background: "var(--accent)", color: "var(--bg)" }}>
              {loading ? "..." : "Load Inventory"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

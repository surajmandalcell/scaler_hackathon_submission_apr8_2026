import { useState } from "react";

export default function MealPlanner({ observation, onSubmit, loading }) {
  const horizon = observation.horizon;
  const inventory = observation.inventory;
  const [days, setDays] = useState(() =>
    Array.from({ length: horizon }, () => [{ name: "", quantity: 100 }])
  );

  const itemNames = inventory.map((i) => i.name);

  const handleIngredientChange = (dayIdx, ingIdx, field, value) => {
    const updated = days.map((d) => d.map((i) => ({ ...i })));
    updated[dayIdx][ingIdx] = {
      ...updated[dayIdx][ingIdx],
      [field]: field === "quantity" ? Number(value) : value,
    };
    setDays(updated);
  };

  const handleAddIngredient = (dayIdx) => {
    const updated = days.map((d) => d.map((i) => ({ ...i })));
    updated[dayIdx].push({ name: "", quantity: 100 });
    setDays(updated);
  };

  const handleRemoveIngredient = (dayIdx, ingIdx) => {
    const updated = days.map((d) => d.map((i) => ({ ...i })));
    updated[dayIdx] = updated[dayIdx].filter((_, i) => i !== ingIdx);
    setDays(updated);
  };

  const handleSubmit = () => {
    const mealPlan = [];
    for (let d = 0; d < days.length; d++) {
      const ingredients = days[d].filter((i) => i.name && i.quantity > 0);
      if (ingredients.length > 0) {
        mealPlan.push({ day: d + 1, meal_name: `day_${d + 1}`, ingredients });
      }
    }
    onSubmit({ meal_plan: mealPlan });
  };

  const s = {
    label: { fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--t4)", textTransform: "uppercase", letterSpacing: "0.06em" },
    input: { padding: "6px 10px", borderRadius: "var(--r)", border: "1px solid var(--line)", background: "var(--bg)", color: "var(--t1)", fontFamily: "var(--mono)", fontSize: "0.78rem", outline: "none" },
    btn: { padding: "5px 12px", borderRadius: "var(--r)", border: "none", cursor: "pointer", fontFamily: "var(--mono)", fontSize: "0.75rem" },
  };

  return (
    <section className="enter" style={{ background: "var(--bg-raised)", border: "1px solid var(--line)", borderRadius: "var(--r-lg)", padding: "32px 36px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h2 style={{ fontFamily: "var(--serif)", fontWeight: 300, fontSize: "1.25rem", color: "var(--t1)" }}>
          Meal Planner
        </h2>
        <button type="button" onClick={handleSubmit} disabled={loading} style={{
          ...s.btn, padding: "7px 20px", fontSize: "0.82rem",
          background: "var(--ok)", color: "var(--bg)", fontFamily: "var(--sans)", fontWeight: 600,
        }}>
          {loading ? "..." : "Submit Plan"}
        </button>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {days.map((ingredients, dayIdx) => (
          <div key={dayIdx} style={{
            padding: "14px 18px", borderRadius: "var(--r)",
            border: "1px solid var(--line)", background: "var(--bg-surface)",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <span style={{ fontFamily: "var(--mono)", fontSize: "0.72rem", color: "var(--t2)", fontWeight: 500 }}>
                Day {dayIdx + 1}
              </span>
              <button type="button" onClick={() => handleAddIngredient(dayIdx)} style={{ ...s.btn, background: "transparent", color: "var(--t3)", border: "1px dashed var(--line)" }}>
                + ingredient
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {ingredients.map((ing, ingIdx) => (
                <div key={ingIdx} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <select value={ing.name} onChange={(e) => handleIngredientChange(dayIdx, ingIdx, "name", e.target.value)}
                    style={{ ...s.input, flex: 1 }}>
                    <option value="">select item...</option>
                    {itemNames.map((n) => <option key={n} value={n}>{n.replace(/_/g, " ")}</option>)}
                  </select>
                  <input type="number" value={ing.quantity} min={1}
                    onChange={(e) => handleIngredientChange(dayIdx, ingIdx, "quantity", e.target.value)}
                    style={{ ...s.input, width: 80 }}
                  />
                  <span style={{ fontFamily: "var(--mono)", fontSize: "0.65rem", color: "var(--t4)" }}>g</span>
                  {ingredients.length > 1 && (
                    <button type="button" onClick={() => handleRemoveIngredient(dayIdx, ingIdx)}
                      style={{ ...s.btn, background: "transparent", color: "var(--danger)", padding: "2px 6px" }}>
                      x
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

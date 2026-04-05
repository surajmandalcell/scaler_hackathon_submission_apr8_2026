import { useCallback, useState } from "react";
import FridgeView from "./components/FridgeView.jsx";
import MealTimeline from "./components/MealTimeline.jsx";
import ScoreCard from "./components/ScoreCard.jsx";
import MealPlanner from "./components/MealPlanner.jsx";
import CustomInventory from "./components/CustomInventory.jsx";
import DocsPage from "./components/DocsPage.jsx";

const TASKS = [
  { id: "easy", label: "Easy" },
  { id: "medium", label: "Medium" },
  { id: "hard", label: "Hard" },
  { id: "custom", label: "Custom" },
];

export default function App() {
  const [page, setPage] = useState("main");
  const [taskId, setTaskId] = useState("easy");
  const [seed, setSeed] = useState(42);
  const [observation, setObservation] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState("idle");

  const handleReset = useCallback(async () => {
    setLoading(true);
    setResult(null);
    setPhase("idle");
    try {
      const resp = await fetch("/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskId, seed: Number(seed) }),
      });
      setObservation(await resp.json());
      setPhase("observing");
    } catch (err) {
      console.error("Reset failed:", err);
    } finally {
      setLoading(false);
    }
  }, [taskId, seed]);

  const handleCustomReset = useCallback(async (customData) => {
    setLoading(true);
    setResult(null);
    setPhase("idle");
    try {
      const resp = await fetch("/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(customData),
      });
      setObservation(await resp.json());
      setPhase("observing");
    } catch (err) {
      console.error("Custom reset failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleStep = useCallback(async (action) => {
    setLoading(true);
    try {
      const resp = await fetch("/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(action || buildFIFOPlan(observation)),
      });
      setResult(await resp.json());
      setPhase("scored");
    } catch (err) {
      console.error("Step failed:", err);
    } finally {
      setLoading(false);
    }
  }, [observation]);

  const isCustom = taskId === "custom";

  // Styles
  const tab = (active) => ({
    padding: "7px 14px", border: "none", cursor: "pointer",
    borderRadius: "var(--r)", fontFamily: "var(--mono)", fontSize: "0.78rem",
    fontWeight: 500, transition: "background 0.15s ease, color 0.15s ease",
    background: active ? "var(--accent)" : "transparent",
    color: active ? "var(--bg)" : "var(--t3)", minWidth: 64, textAlign: "center",
  });

  return (
    <div style={{ maxWidth: 980, margin: "0 auto", padding: "56px 32px 96px" }}>

      {/* ── Header ── */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 48 }}>
        <div>
          <h1 style={{
            fontFamily: "var(--serif)", fontWeight: 300, fontSize: "2.4rem",
            letterSpacing: "-0.03em", color: "var(--t1)", lineHeight: 1.1,
            cursor: "pointer",
          }} onClick={() => setPage("main")}>
            FridgeEnv
          </h1>
          <p style={{ fontFamily: "var(--mono)", fontSize: "0.78rem", color: "var(--t3)", marginTop: 6, letterSpacing: "0.01em" }}>
            Food waste reduction benchmark for RL agents
          </p>
        </div>
        <button type="button" onClick={() => setPage(page === "docs" ? "main" : "docs")} style={{
          ...tab(page === "docs"), marginTop: 8,
        }}>
          {page === "docs" ? "Back" : "Docs"}
        </button>
      </header>

      {/* ── Docs Page ── */}
      {page === "docs" && <DocsPage />}

      {/* ── Main Page ── */}
      {page === "main" && (
        <>
          {/* Controls */}
          <div className="enter" style={{
            display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap",
            marginBottom: 48, paddingBottom: 28, borderBottom: "1px solid var(--line)",
          }}>
            <div style={{ display: "flex", gap: 2 }}>
              {TASKS.map((t) => (
                <button type="button" key={t.id} onClick={() => { setTaskId(t.id); setObservation(null); setResult(null); setPhase("idle"); }} style={tab(taskId === t.id)}>
                  {t.label}
                </button>
              ))}
            </div>

            {!isCustom && (
              <>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <label htmlFor="seed" style={{ fontFamily: "var(--mono)", fontSize: "0.7rem", color: "var(--t4)", textTransform: "uppercase", letterSpacing: "0.06em" }}>Seed</label>
                  <input id="seed" type="number" value={seed} onChange={(e) => setSeed(e.target.value)}
                    style={{ width: 64, padding: "6px 10px", borderRadius: "var(--r)", border: "1px solid var(--line)", background: "var(--bg-raised)", color: "var(--t1)", fontFamily: "var(--mono)", fontSize: "0.82rem", outline: "none" }}
                  />
                </div>
                <button type="button" onClick={handleReset} disabled={loading} style={{
                  padding: "7px 20px", borderRadius: "var(--r)",
                  border: "1px solid var(--accent-border)", background: "var(--accent-dim)",
                  color: "var(--accent)", cursor: loading ? "wait" : "pointer",
                  fontFamily: "var(--sans)", fontSize: "0.82rem", fontWeight: 600,
                }}>
                  {loading && phase === "idle" ? "..." : "Generate"}
                </button>
              </>
            )}

            {observation && phase === "observing" && (
              <button type="button" onClick={() => handleStep(null)} disabled={loading} style={{
                padding: "7px 20px", borderRadius: "var(--r)",
                border: "1px solid rgba(107,155,90,0.3)", background: "rgba(107,155,90,0.08)",
                color: "var(--ok)", cursor: loading ? "wait" : "pointer",
                fontFamily: "var(--sans)", fontSize: "0.82rem", fontWeight: 600,
              }}>
                {loading ? "..." : "Run FIFO Agent"}
              </button>
            )}
          </div>

          {/* Custom inventory input */}
          {isCustom && !observation && (
            <CustomInventory onSubmit={handleCustomReset} loading={loading} />
          )}

          {/* Content */}
          {observation && (
            <div style={{ display: "flex", flexDirection: "column", gap: 36 }}>
              <FridgeView
                inventory={observation.inventory}
                currentDate={observation.current_date}
                horizon={observation.horizon}
                householdSize={observation.household_size}
                restrictions={observation.dietary_restrictions}
              />

              {/* Manual meal planner — shown before scoring */}
              {phase === "observing" && (
                <MealPlanner observation={observation} onSubmit={handleStep} loading={loading} />
              )}

              {result && <ScoreCard reward={result.reward} />}
              {result?.info && (
                <MealTimeline
                  consumptionLog={result.info.consumption_log}
                  nutritionLog={result.info.nutrition_log}
                  horizon={observation.horizon}
                  expiryEvents={result.info.expiry_events}
                />
              )}
            </div>
          )}

          {/* Empty state */}
          {!observation && !isCustom && phase === "idle" && (
            <div style={{ textAlign: "center", padding: "96px 20px", color: "var(--t4)" }}>
              <p style={{ fontFamily: "var(--serif)", fontSize: "1.1rem", fontWeight: 300, fontStyle: "italic" }}>
                Choose a difficulty and generate a fridge to begin
              </p>
            </div>
          )}
        </>
      )}

      {/* ── Footer ── */}
      <footer style={{
        marginTop: 80, paddingTop: 20, borderTop: "1px solid var(--line)",
        color: "var(--t4)", fontSize: "0.7rem", fontFamily: "var(--mono)",
        display: "flex", justifyContent: "space-between",
      }}>
        <span>FridgeEnv v1.0</span>
        <span>Scaler x Meta PyTorch Hackathon 2026</span>
      </footer>
    </div>
  );
}

function buildFIFOPlan(observation) {
  const inv = [...observation.inventory].sort((a, b) => a.expiry_date.localeCompare(b.expiry_date));
  const avail = {};
  for (const i of inv) avail[i.name] = i.quantity;

  const plan = [];
  for (let day = 1; day <= observation.horizon; day++) {
    const ing = [];
    const used = new Set();
    for (const item of inv) {
      if (used.size >= 4) break;
      if (avail[item.name] <= 0 || used.has(item.name)) continue;
      const qty = avail[item.name] * 0.4;
      if (qty > 0) {
        ing.push({ name: item.name, quantity: Math.round(qty * 10) / 10 });
        avail[item.name] -= qty;
        used.add(item.name);
      }
    }
    if (ing.length) plan.push({ day, meal_name: `day_${day}`, ingredients: ing });
  }
  return { meal_plan: plan };
}

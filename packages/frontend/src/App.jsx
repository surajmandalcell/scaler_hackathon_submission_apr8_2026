import { useCallback, useState } from "react";
import FridgeView from "./components/FridgeView.jsx";
import MealTimeline from "./components/MealTimeline.jsx";
import ScoreCard from "./components/ScoreCard.jsx";

const TASKS = [
  { id: "easy", label: "Easy", sub: "3d / 5-8 items" },
  { id: "medium", label: "Medium", sub: "7d / 10-15 items" },
  { id: "hard", label: "Hard", sub: "14d / 20-30 items" },
];

export default function App() {
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

  const handleStep = useCallback(async () => {
    if (!observation) return;
    setLoading(true);
    try {
      const inv = [...observation.inventory].sort((a, b) =>
        a.expiry_date.localeCompare(b.expiry_date)
      );
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

      const resp = await fetch("/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ meal_plan: plan }),
      });
      setResult(await resp.json());
      setPhase("scored");
    } catch (err) {
      console.error("Step failed:", err);
    } finally {
      setLoading(false);
    }
  }, [observation]);

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: "48px 24px 80px" }}>

      {/* ── Header ── */}
      <header style={{ marginBottom: 48 }}>
        <h1 style={{
          fontFamily: "var(--serif)", fontWeight: 300, fontSize: "2.4rem",
          letterSpacing: "-0.03em", color: "var(--t1)", lineHeight: 1.1,
        }}>
          FridgeEnv
        </h1>
        <p style={{
          fontFamily: "var(--mono)", fontSize: "0.78rem", color: "var(--t3)",
          marginTop: 6, letterSpacing: "0.01em",
        }}>
          Food waste reduction benchmark for RL agents
        </p>
      </header>

      {/* ── Controls ── */}
      <div className="enter" style={{
        display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap",
        marginBottom: 40, paddingBottom: 24, borderBottom: "1px solid var(--line)",
      }}>
        {/* Task pills */}
        <div style={{ display: "flex", gap: 2 }}>
          {TASKS.map((t) => {
            const active = taskId === t.id;
            return (
              <button type="button" key={t.id} onClick={() => setTaskId(t.id)} style={{
                padding: "7px 14px", border: "none", cursor: "pointer",
                borderRadius: "var(--r)", fontFamily: "var(--sans)", fontSize: "0.82rem",
                fontWeight: active ? 600 : 400, transition: "all 0.15s ease",
                background: active ? "var(--accent)" : "transparent",
                color: active ? "var(--bg)" : "var(--t3)",
              }}>
                {t.label}
              </button>
            );
          })}
        </div>

        {/* Seed */}
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <label htmlFor="seed" style={{
            fontFamily: "var(--mono)", fontSize: "0.7rem", color: "var(--t4)",
            textTransform: "uppercase", letterSpacing: "0.06em",
          }}>Seed</label>
          <input id="seed" type="number" value={seed}
            onChange={(e) => setSeed(e.target.value)}
            style={{
              width: 64, padding: "6px 10px", borderRadius: "var(--r)",
              border: "1px solid var(--line)", background: "var(--bg-raised)",
              color: "var(--t1)", fontFamily: "var(--mono)", fontSize: "0.82rem",
              outline: "none",
            }}
          />
        </div>

        {/* Buttons */}
        <button type="button" onClick={handleReset} disabled={loading} style={{
          padding: "7px 20px", borderRadius: "var(--r)",
          border: "1px solid var(--accent-border)", background: "var(--accent-dim)",
          color: "var(--accent)", cursor: loading ? "wait" : "pointer",
          fontFamily: "var(--sans)", fontSize: "0.82rem", fontWeight: 600,
        }}>
          {loading && phase === "idle" ? "..." : "Generate"}
        </button>

        {observation && phase === "observing" && (
          <button type="button" onClick={handleStep} disabled={loading} style={{
            padding: "7px 20px", borderRadius: "var(--r)",
            border: "1px solid rgba(107,155,90,0.3)", background: "rgba(107,155,90,0.08)",
            color: "var(--ok)", cursor: loading ? "wait" : "pointer",
            fontFamily: "var(--sans)", fontSize: "0.82rem", fontWeight: 600,
          }}>
            {loading ? "..." : "Run FIFO Agent"}
          </button>
        )}
      </div>

      {/* ── Content ── */}
      {observation && (
        <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
          <FridgeView
            inventory={observation.inventory}
            currentDate={observation.current_date}
            horizon={observation.horizon}
            householdSize={observation.household_size}
            restrictions={observation.dietary_restrictions}
          />
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

      {/* ── Empty state ── */}
      {!observation && phase === "idle" && (
        <div style={{ textAlign: "center", padding: "96px 20px", color: "var(--t4)" }}>
          <p style={{ fontFamily: "var(--serif)", fontSize: "1.1rem", fontWeight: 300, fontStyle: "italic" }}>
            Choose a difficulty and generate a fridge to begin
          </p>
        </div>
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

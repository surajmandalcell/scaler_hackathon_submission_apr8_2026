import React, { useState, useCallback } from "react";
import FridgeView from "./components/FridgeView.jsx";
import MealTimeline from "./components/MealTimeline.jsx";
import ScoreCard from "./components/ScoreCard.jsx";

const TASKS = [
  { id: "easy", label: "Easy", desc: "3 days, 5-8 items" },
  { id: "medium", label: "Medium", desc: "7 days, 10-15 items" },
  { id: "hard", label: "Hard", desc: "14 days, 20-30 items" },
];

export default function App() {
  const [taskId, setTaskId] = useState("easy");
  const [seed, setSeed] = useState(42);
  const [observation, setObservation] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState("idle"); // idle | observing | scored

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
      const data = await resp.json();
      setObservation(data);
      setPhase("observing");
    } catch (err) {
      console.error("Reset failed:", err);
    } finally {
      setLoading(false);
    }
  }, [taskId, seed]);

  const handleRunFIFO = useCallback(async () => {
    if (!observation) return;
    setLoading(true);
    try {
      // Build a FIFO-style plan client-side
      const inv = [...observation.inventory].sort(
        (a, b) => a.expiry_date.localeCompare(b.expiry_date)
      );
      const available = {};
      inv.forEach((i) => (available[i.name] = i.quantity));

      const mealPlan = [];
      for (let day = 1; day <= observation.horizon; day++) {
        const ingredients = [];
        const used = new Set();
        // Pick soonest-expiring items
        for (const item of inv) {
          if (used.size >= 4) break;
          if (available[item.name] <= 0 || used.has(item.name)) continue;
          const portion = Math.min(
            available[item.name],
            available[item.name] * 0.4
          );
          if (portion > 0) {
            ingredients.push({ name: item.name, quantity: Math.round(portion * 10) / 10 });
            available[item.name] -= portion;
            used.add(item.name);
          }
        }
        if (ingredients.length > 0) {
          mealPlan.push({ day, meal_name: `day_${day}_meal`, ingredients });
        }
      }

      const resp = await fetch("/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ meal_plan: mealPlan }),
      });
      const data = await resp.json();
      setResult(data);
      setPhase("scored");
    } catch (err) {
      console.error("Step failed:", err);
    } finally {
      setLoading(false);
    }
  }, [observation]);

  return (
    <div style={{ maxWidth: 1280, margin: "0 auto", padding: "32px 24px" }}>
      {/* Header */}
      <header style={{ marginBottom: 40, textAlign: "center" }}>
        <h1
          style={{
            fontFamily: "var(--font-display)",
            fontSize: "clamp(2rem, 5vw, 3.2rem)",
            fontWeight: 400,
            letterSpacing: "-0.02em",
            marginBottom: 8,
            background: "linear-gradient(135deg, var(--accent), var(--yellow-warning))",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          FridgeEnv
        </h1>
        <p
          style={{
            fontFamily: "var(--font-body)",
            color: "var(--text-secondary)",
            fontSize: "1.05rem",
            fontWeight: 300,
            letterSpacing: "0.02em",
          }}
        >
          Food Waste Reduction — RL Benchmark
        </p>
      </header>

      {/* Controls */}
      <div
        className="fade-in"
        style={{
          display: "flex",
          gap: 12,
          justifyContent: "center",
          alignItems: "center",
          flexWrap: "wrap",
          marginBottom: 32,
        }}
      >
        {/* Task selector */}
        <div style={{ display: "flex", gap: 4, background: "var(--bg-card)", borderRadius: "var(--radius)", padding: 4 }}>
          {TASKS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTaskId(t.id)}
              style={{
                padding: "8px 16px",
                borderRadius: "var(--radius-sm)",
                border: "none",
                cursor: "pointer",
                fontFamily: "var(--font-body)",
                fontSize: "0.85rem",
                fontWeight: 500,
                transition: "all 0.2s",
                background: taskId === t.id ? "var(--accent)" : "transparent",
                color: taskId === t.id ? "#000" : "var(--text-secondary)",
              }}
              title={t.desc}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Seed input */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <label style={{ color: "var(--text-muted)", fontSize: "0.8rem", fontFamily: "var(--font-mono)" }}>
            SEED
          </label>
          <input
            type="number"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            style={{
              width: 72,
              padding: "8px 12px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border)",
              background: "var(--bg-card)",
              color: "var(--text-primary)",
              fontFamily: "var(--font-mono)",
              fontSize: "0.85rem",
              outline: "none",
            }}
          />
        </div>

        {/* Action buttons */}
        <button
          onClick={handleReset}
          disabled={loading}
          style={{
            padding: "8px 24px",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--border-accent)",
            background: "var(--accent-soft)",
            color: "var(--accent)",
            cursor: loading ? "wait" : "pointer",
            fontFamily: "var(--font-body)",
            fontSize: "0.85rem",
            fontWeight: 600,
            transition: "all 0.2s",
          }}
        >
          {loading && phase === "idle" ? "Loading..." : "Reset"}
        </button>

        {observation && phase === "observing" && (
          <button
            onClick={handleRunFIFO}
            disabled={loading}
            style={{
              padding: "8px 24px",
              borderRadius: "var(--radius-sm)",
              border: "none",
              background: "var(--green-muted)",
              color: "#000",
              cursor: loading ? "wait" : "pointer",
              fontFamily: "var(--font-body)",
              fontSize: "0.85rem",
              fontWeight: 600,
              transition: "all 0.2s",
              animation: "fadeInUp 0.3s ease-out",
            }}
          >
            {loading ? "Planning..." : "Run FIFO Agent"}
          </button>
        )}
      </div>

      {/* Main content */}
      {observation && (
        <div style={{ display: "grid", gap: 24 }}>
          {/* Fridge Inventory */}
          <FridgeView
            inventory={observation.inventory}
            currentDate={observation.current_date}
            horizon={observation.horizon}
            householdSize={observation.household_size}
            restrictions={observation.dietary_restrictions}
          />

          {/* Score Card (after step) */}
          {result && <ScoreCard reward={result.reward} info={result.info} />}

          {/* Meal Timeline (after step) */}
          {result && result.info && (
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
      {!observation && phase === "idle" && (
        <div
          style={{
            textAlign: "center",
            padding: "80px 20px",
            color: "var(--text-muted)",
          }}
        >
          <div style={{ fontSize: "3rem", marginBottom: 16, opacity: 0.4 }}>
            🥦
          </div>
          <p style={{ fontFamily: "var(--font-body)", fontSize: "1rem", fontWeight: 300 }}>
            Select a difficulty and click <strong style={{ color: "var(--accent)" }}>Reset</strong> to generate a fridge
          </p>
        </div>
      )}

      {/* Footer */}
      <footer
        style={{
          marginTop: 64,
          paddingTop: 24,
          borderTop: "1px solid var(--border)",
          textAlign: "center",
          color: "var(--text-muted)",
          fontSize: "0.75rem",
          fontFamily: "var(--font-mono)",
        }}
      >
        FridgeEnv v1.0 — Scaler x Meta PyTorch Hackathon 2026
      </footer>
    </div>
  );
}

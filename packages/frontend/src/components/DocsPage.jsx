export default function DocsPage() {
  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>
      <Section title="What is FridgeEnv">
        <P>An OpenEnv-compliant RL environment that simulates household food waste. Agents receive a fridge inventory with expiring items and must create meal plans that minimize waste while respecting dietary restrictions.</P>
        <P>This is a <strong>benchmark environment</strong> — we build the gym, researchers train their agents against it.</P>
      </Section>

      <Section title="How the Pipeline Works">
        <Step n="1" label="Generate">
          <Code>POST /reset {`{"task_id": "hard", "seed": 42}`}</Code>
          <P>A seeded RNG generates a deterministic fridge scenario: N items with expiry dates, dietary restrictions, and a planning horizon. Same seed always produces the same fridge — essential for reproducible benchmarks.</P>
        </Step>
        <Step n="2" label="Decide">
          <P>An agent (heuristic, LLM, or RL model) examines the inventory and produces a meal plan: which items to use on which days, in what quantities.</P>
        </Step>
        <Step n="3" label="Simulate">
          <Code>POST /step {`{"meal_plan": [...]}`}</Code>
          <P>The environment simulates the plan day by day: deducts inventory, expires items past their date, checks dietary violations, tracks nutrition balance.</P>
        </Step>
        <Step n="4" label="Score">
          <P>The grader computes a score from 0.0 to 1.0: what fraction of perishable items were used before expiring. Additional signals: waste rate, nutrition score, violation count.</P>
        </Step>
      </Section>

      <Section title="API Reference">
        <Endpoint method="GET" path="/health" desc="Health check" example={{
          response: `{"status": "healthy"}`
        }} />
        <Endpoint method="GET" path="/metadata" desc="Environment metadata" example={{
          response: `{"name": "FridgeEnv", "description": "...", "version": "1.0.0", "tasks": ["easy", "medium", "hard"]}`
        }} />
        <Endpoint method="POST" path="/reset" desc="Start a new episode" example={{
          request: `{"task_id": "medium", "seed": 42}`,
          requestAlt: `{"inventory": [...], "horizon": 7, "household_size": 3, "dietary_restrictions": ["vegetarian"]}`,
          response: `{"inventory": [...], "current_date": "2026-01-01", "horizon": 7, "household_size": 3, "dietary_restrictions": ["vegetarian"], "done": false}`
        }} />
        <Endpoint method="POST" path="/step" desc="Submit a meal plan" example={{
          request: `{"meal_plan": [{"day": 1, "meal_name": "stir_fry", "ingredients": [{"name": "chicken_breast", "quantity": 250}]}]}`,
          response: `{"observation": {...}, "reward": {"score": 0.85, "waste_rate": 0.15, "nutrition_score": 0.67, ...}, "done": true}`
        }} />
        <Endpoint method="GET" path="/state" desc="Current episode state" example={{
          response: `{"task_id": "medium", "seed": 42, "done": true, "inventory": [...], "reward": {...}}`
        }} />
        <Endpoint method="GET" path="/schema" desc="Action/Observation/State JSON schemas" />
        <Endpoint method="POST" path="/mcp" desc="MCP JSON-RPC endpoint (OpenEnv spec)" />
      </Section>

      <Section title="Data Models">
        <Model name="Observation" fields={[
          ["inventory", "FridgeItem[]", "Items in the fridge"],
          ["current_date", "string (ISO date)", "Simulation start date"],
          ["horizon", "int (3-14)", "Days to plan for"],
          ["household_size", "int (2-4)", "Number of people"],
          ["dietary_restrictions", "string[]", "e.g. vegetarian, lactose-free"],
          ["done", "bool", "Episode complete?"],
          ["reward", "float | null", "Grader score when done"],
        ]} />
        <Model name="Action" fields={[
          ["meal_plan", "Meal[]", "List of daily meals"],
        ]} />
        <Model name="Meal" fields={[
          ["day", "int (>=1)", "Which day this meal is for"],
          ["meal_name", "string", "Name of the meal"],
          ["ingredients", "MealIngredient[]", "Items and quantities used"],
        ]} />
        <Model name="Reward" fields={[
          ["score", "float (0-1)", "Grader: used_perishables / total_perishables"],
          ["waste_rate", "float", "Fraction of items that expired unused"],
          ["nutrition_score", "float", "Fraction of days with balanced meals"],
          ["items_used", "int", "Count of items with any consumption"],
          ["items_expired", "int", "Count of items that expired with remainder"],
          ["violations", "string[]", "Dietary restriction breaches"],
        ]} />
      </Section>

      <Section title="Difficulty Levels">
        <div style={{ fontFamily: "var(--mono)", fontSize: "0.78rem" }}>
          <Row cells={["", "Items", "Horizon", "People", "Restrictions"]} header />
          <Row cells={["Easy", "5-8", "3 days", "2", "none"]} />
          <Row cells={["Medium", "10-15", "7 days", "3", "1"]} />
          <Row cells={["Hard", "20-30", "14 days", "4", "2"]} />
        </div>
      </Section>

      <Section title="Baseline Scores">
        <div style={{ fontFamily: "var(--mono)", fontSize: "0.78rem" }}>
          <Row cells={["Agent", "Easy", "Medium", "Hard"]} header />
          <Row cells={["Random", "0.72", "0.66", "0.63"]} />
          <Row cells={["FIFO", "1.00", "0.99", "0.99"]} />
          <Row cells={["GLM-5.1", "0.97", "0.73", "0.68"]} />
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section style={{ marginBottom: 40 }}>
      <h2 style={{ fontFamily: "var(--serif)", fontWeight: 300, fontSize: "1.3rem", color: "var(--t1)", marginBottom: 12, paddingBottom: 8, borderBottom: "1px solid var(--line)" }}>
        {title}
      </h2>
      {children}
    </section>
  );
}

function P({ children }) {
  return <p style={{ fontFamily: "var(--sans)", fontSize: "0.88rem", color: "var(--t2)", lineHeight: 1.65, marginBottom: 10 }}>{children}</p>;
}

function Code({ children }) {
  return (
    <pre style={{ fontFamily: "var(--mono)", fontSize: "0.75rem", color: "var(--t2)", background: "var(--bg-surface)", border: "1px solid var(--line)", borderRadius: "var(--r)", padding: "10px 14px", marginBottom: 10, overflowX: "auto", whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
      {children}
    </pre>
  );
}

function Step({ n, label, children }) {
  return (
    <div style={{ marginBottom: 16, paddingLeft: 20, borderLeft: "2px solid var(--line)" }}>
      <div style={{ fontFamily: "var(--mono)", fontSize: "0.68rem", color: "var(--accent)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>
        Step {n} — {label}
      </div>
      {children}
    </div>
  );
}

function Endpoint({ method, path, desc, example }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 4 }}>
        <span style={{ fontFamily: "var(--mono)", fontSize: "0.68rem", fontWeight: 500, color: method === "GET" ? "var(--ok)" : "var(--accent)", padding: "2px 6px", background: method === "GET" ? "rgba(107,155,90,0.08)" : "var(--accent-dim)", borderRadius: "var(--r)" }}>
          {method}
        </span>
        <span style={{ fontFamily: "var(--mono)", fontSize: "0.82rem", color: "var(--t1)" }}>{path}</span>
        <span style={{ fontFamily: "var(--sans)", fontSize: "0.8rem", color: "var(--t3)" }}>{desc}</span>
      </div>
      {example?.request && <Code>Request: {example.request}</Code>}
      {example?.requestAlt && <Code>Alt request: {example.requestAlt}</Code>}
      {example?.response && <Code>Response: {example.response}</Code>}
    </div>
  );
}

function Model({ name, fields }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ fontFamily: "var(--mono)", fontSize: "0.8rem", color: "var(--accent)", fontWeight: 500, marginBottom: 6 }}>{name}</div>
      <div style={{ fontSize: "0.78rem", fontFamily: "var(--mono)" }}>
        {fields.map(([field, type, desc]) => (
          <div key={field} style={{ display: "grid", gridTemplateColumns: "140px 160px 1fr", gap: 8, padding: "4px 0", borderBottom: "1px solid var(--line)" }}>
            <span style={{ color: "var(--t1)" }}>{field}</span>
            <span style={{ color: "var(--t3)" }}>{type}</span>
            <span style={{ color: "var(--t3)", fontFamily: "var(--sans)" }}>{desc}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Row({ cells, header }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(${cells.length}, 1fr)`, gap: 8, padding: "6px 0", borderBottom: "1px solid var(--line)", color: header ? "var(--t4)" : "var(--t2)", fontWeight: header ? 500 : 400 }}>
      {cells.map((c, i) => <span key={i}>{c}</span>)}
    </div>
  );
}

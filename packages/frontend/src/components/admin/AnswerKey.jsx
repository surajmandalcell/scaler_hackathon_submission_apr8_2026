import { useEffect, useState } from "react";

const DIFFICULTIES = [
  { id: "easy",   label: "Easy" },
  { id: "medium", label: "Medium" },
  { id: "hard",   label: "Hard" },
];

function fmt(v) {
  if (v == null || v === "") return "—";
  if (typeof v === "number") return v.toFixed(4);
  return String(v);
}

export default function AnswerKey({ taskId, setTaskId }) {
  const [answers, setAnswers] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    fetch(`/api/admin/answer-key/json?task_id=${taskId}`)
      .then((r) => r.json())
      .then((body) => {
        if (!alive) return;
        if (body.error) setError(body.error);
        else setAnswers(body.answers || {});
      })
      .catch((err) => alive && setError(err.message))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [taskId]);

  function handleDownloadXlsx() {
    const a = document.createElement("a");
    a.href = "/api/admin/answer-key";
    a.download = "fundlens_answer_key.xlsx";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  const funds = answers ? Object.entries(answers) : [];

  return (
    <div className="md-stack-lg">
      <section className="md-card">
        <div className="md-stack">
          <div className="md-stack-sm">
            <span className="md-label-large md-on-surface-variant">Task</span>
            <div className="md-row" role="group" aria-label="Difficulty">
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  className={`md-chip ${taskId === d.id ? "is-selected" : ""}`}
                  onClick={() => setTaskId(d.id)}
                  aria-pressed={taskId === d.id}
                >
                  {d.label}
                </button>
              ))}
            </div>
            <p className="md-body-small md-on-surface-variant">
              Computed against a throwaway store — safe to browse without
              disturbing the Playground session or the Analyst scenario.
            </p>
          </div>

          <div className="md-row">
            <button
              type="button"
              className="md-btn md-btn-filled"
              onClick={handleDownloadXlsx}
            >
              Download answer key (xlsx)
            </button>
          </div>
        </div>
      </section>

      {loading && <p className="md-body-medium md-on-surface-variant">Loading answers…</p>}

      {error && (
        <div className="md-card" style={{ background: "var(--md-error-container)" }}>
          <p style={{ color: "var(--md-on-error-container)" }}>{error}</p>
        </div>
      )}

      {funds.length > 0 && (
        <div className="md-stack-lg">
          {funds.map(([fid, fund]) => (
            <section key={fid} className="md-stack">
              <div className="md-stack-sm">
                <span className="md-eyebrow">{fid}</span>
                <h3 className="md-headline-small">{fund.fund_name}</h3>
              </div>

              <div className="md-table-wrap">
                <table className="md-table">
                  <thead>
                    <tr>
                      <th>Line</th>
                      <th style={{ textAlign: "right" }}>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(fund.nav_bridge || {}).map(([k, v]) => (
                      <tr key={k}>
                        <td>{k}</td>
                        <td className="md-mono" style={{ textAlign: "right" }}>{fmt(v)}</td>
                      </tr>
                    ))}
                    {Object.entries(fund.metrics || {}).map(([k, v]) => (
                      <tr key={`m-${k}`}>
                        <td><em>{k}</em></td>
                        <td className="md-mono" style={{ textAlign: "right" }}>{fmt(v)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

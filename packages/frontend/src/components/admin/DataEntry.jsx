import { useState } from "react";

// Minimal CRUD forms for the four store entities. Each form POSTs to its
// corresponding /api/admin/* endpoint and surfaces a compact status line
// (success or error). After any mutation, `onStoreMutated` is called so the
// parent can refresh the portfolio data backing the Analyst/Investor views.

const SECTORS = ["Office", "Residential", "Retail", "Logistics", "Data Center", "Other"];
const CF_TYPES = [
  { id: "contribution", label: "Contribution (capital call — negative)" },
  { id: "disposition",  label: "Disposition (sale proceeds — positive)"  },
  { id: "income",       label: "Income (rent/yield — positive)"          },
];

function Form({ title, children, onSubmit, status }) {
  return (
    <section className="md-card">
      <div className="md-stack">
        <h3 className="md-headline-small">{title}</h3>
        <form onSubmit={onSubmit} className="md-stack">
          {children}
        </form>
        {status && (
          <p
            className={`md-body-small md-mono ${status.ok ? "md-pos" : "md-error-text"}`}
          >
            {status.msg}
          </p>
        )}
      </div>
    </section>
  );
}

async function postJson(path, body) {
  const resp = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return resp.json();
}

export default function DataEntry({ onStoreMutated, scenario }) {
  const fundIds = scenario?.portfolio ? Object.keys(scenario.portfolio) : [];
  const [fundStatus, setFundStatus] = useState(null);
  const [dealStatus, setDealStatus] = useState(null);
  const [ownStatus, setOwnStatus] = useState(null);
  const [cfStatus, setCfStatus] = useState(null);

  function notify(setter, body, successKey = "ok") {
    if (body && body.error) {
      setter({ ok: false, msg: `✘ ${body.error}` });
    } else {
      setter({
        ok: true,
        msg: `✔ ${successKey in body ? JSON.stringify(body) : "done"}`,
      });
      onStoreMutated?.();
    }
  }

  async function handleFundSubmit(e) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const body = {
      fund_name: fd.get("fund_name"),
      fund_currency: fd.get("fund_currency") || "USD",
      reporting_date: fd.get("reporting_date") || "",
      beginning_nav: Number(fd.get("beginning_nav") || 0),
      ending_nav: Number(fd.get("ending_nav") || 0),
      nav_period_start: fd.get("nav_period_start") || "",
    };
    notify(setFundStatus, await postJson("/api/admin/fund", body));
    e.currentTarget.reset();
  }

  async function handleDealSubmit(e) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const body = {
      property_name: fd.get("property_name"),
      sector: fd.get("sector") || "Other",
      location: fd.get("location") || "",
      appraiser_nav: Number(fd.get("appraiser_nav") || 0),
    };
    notify(setDealStatus, await postJson("/api/admin/deal", body));
    e.currentTarget.reset();
  }

  async function handleOwnershipSubmit(e) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const body = {
      fund_id: fd.get("fund_id"),
      deal_id: fd.get("deal_id"),
      ownership_pct: Number(fd.get("ownership_pct") || 1.0),
      entry_date: fd.get("entry_date") || "",
    };
    notify(setOwnStatus, await postJson("/api/admin/ownership", body));
    e.currentTarget.reset();
  }

  async function handleCashflowSubmit(e) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const body = {
      fund_id: fd.get("fund_id"),
      deal_id: fd.get("deal_id"),
      cash_date: fd.get("cash_date"),
      cf_type: fd.get("cf_type"),
      fund_amt: Number(fd.get("fund_amt") || 0),
    };
    notify(setCfStatus, await postJson("/api/admin/cashflow", body));
    e.currentTarget.reset();
  }

  async function handleRecompute() {
    const resp = await fetch("/api/admin/recompute", { method: "POST" });
    await resp.json();
    onStoreMutated?.();
  }

  async function handleClear() {
    if (!confirm("Clear the entire store? This cannot be undone.")) return;
    await fetch("/api/admin/clear", { method: "POST" });
    onStoreMutated?.();
  }

  return (
    <div className="md-stack-lg">
      <div className="md-grid md-grid-auto" style={{ alignItems: "start" }}>
        {/* ── Fund ────────────────────────────────────────────────────── */}
        <Form title="Add fund" status={fundStatus} onSubmit={handleFundSubmit}>
          <label className="md-field">
            <span className="md-field-label">Fund name *</span>
            <input className="md-select" name="fund_name" required placeholder="RE Alpha Fund I" />
          </label>
          <div className="md-row">
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Currency</span>
              <input className="md-select" name="fund_currency" defaultValue="USD" />
            </label>
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Reporting date</span>
              <input className="md-select" name="reporting_date" type="date" />
            </label>
          </div>
          <div className="md-row">
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Beginning NAV ($M)</span>
              <input className="md-select" name="beginning_nav" type="number" step="0.01" defaultValue="0" />
            </label>
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Ending NAV ($M)</span>
              <input className="md-select" name="ending_nav" type="number" step="0.01" defaultValue="0" />
            </label>
          </div>
          <label className="md-field">
            <span className="md-field-label">NAV period start</span>
            <input className="md-select" name="nav_period_start" type="date" />
          </label>
          <button type="submit" className="md-btn md-btn-filled">Add fund</button>
        </Form>

        {/* ── Deal ────────────────────────────────────────────────────── */}
        <Form title="Add property" status={dealStatus} onSubmit={handleDealSubmit}>
          <label className="md-field">
            <span className="md-field-label">Property name *</span>
            <input className="md-select" name="property_name" required placeholder="Embassy Office" />
          </label>
          <div className="md-row">
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Sector</span>
              <select className="md-select" name="sector" defaultValue="Other">
                {SECTORS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Location</span>
              <input className="md-select" name="location" placeholder="Bangalore" />
            </label>
          </div>
          <label className="md-field">
            <span className="md-field-label">Appraiser NAV ($M)</span>
            <input className="md-select" name="appraiser_nav" type="number" step="0.01" defaultValue="0" />
          </label>
          <button type="submit" className="md-btn md-btn-filled">Add property</button>
        </Form>

        {/* ── Ownership ───────────────────────────────────────────────── */}
        <Form title="Link fund ↔ property" status={ownStatus} onSubmit={handleOwnershipSubmit}>
          <label className="md-field">
            <span className="md-field-label">Fund ID *</span>
            <select className="md-select" name="fund_id" required defaultValue="">
              <option value="" disabled>Pick a fund…</option>
              {fundIds.map((fid) => (
                <option key={fid} value={fid}>
                  {scenario.portfolio[fid]?.fund_name || fid}
                </option>
              ))}
            </select>
          </label>
          <label className="md-field">
            <span className="md-field-label">Deal ID *</span>
            <input className="md-select" name="deal_id" required placeholder="embassy_office" />
          </label>
          <div className="md-row">
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Ownership (0.0–1.0)</span>
              <input className="md-select" name="ownership_pct" type="number" step="0.01" min="0" max="1" defaultValue="1.0" />
            </label>
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Entry date</span>
              <input className="md-select" name="entry_date" type="date" />
            </label>
          </div>
          <button type="submit" className="md-btn md-btn-filled">Link</button>
        </Form>

        {/* ── Cashflow ────────────────────────────────────────────────── */}
        <Form title="Add cashflow" status={cfStatus} onSubmit={handleCashflowSubmit}>
          <div className="md-row">
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Fund ID *</span>
              <select className="md-select" name="fund_id" required defaultValue="">
                <option value="" disabled>Pick a fund…</option>
                {fundIds.map((fid) => (
                  <option key={fid} value={fid}>
                    {scenario.portfolio[fid]?.fund_name || fid}
                  </option>
                ))}
              </select>
            </label>
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Deal ID *</span>
              <input className="md-select" name="deal_id" required placeholder="embassy_office" />
            </label>
          </div>
          <div className="md-row">
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Date *</span>
              <input className="md-select" name="cash_date" type="date" required />
            </label>
            <label className="md-field" style={{ flex: 1 }}>
              <span className="md-field-label">Type *</span>
              <select className="md-select" name="cf_type" required defaultValue="contribution">
                {CF_TYPES.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
              </select>
            </label>
          </div>
          <label className="md-field">
            <span className="md-field-label">Fund amount ($M) — negative for contribution</span>
            <input className="md-select" name="fund_amt" type="number" step="0.0001" required />
          </label>
          <button type="submit" className="md-btn md-btn-filled">Add cashflow</button>
        </Form>
      </div>

      {/* ── Store-level actions ─────────────────────────────────────── */}
      <section className="md-card">
        <div className="md-stack">
          <h3 className="md-headline-small">Store actions</h3>
          <p className="md-body-medium md-on-surface-variant">
            After adding deals and ownerships, recompute NAVs to push the
            appraiser values up to the fund level. Clearing wipes both the
            in-memory cache and the SQLite backing store.
          </p>
          <div className="md-row">
            <button type="button" className="md-btn md-btn-tonal" onClick={handleRecompute}>
              Recompute fund NAVs
            </button>
            <button type="button" className="md-btn md-btn-outlined" onClick={handleClear}>
              Clear store
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}

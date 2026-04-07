import { useState } from "react";

// Drop-zone-ish upload surface for the two xlsx templates. The zones aren't
// "drag-and-drop" native yet (just a styled file input); that's a
// straight-forward future upgrade once we confirm the core upload path works.

function UploadCard({
  title,
  description,
  templateUrl,
  templateFilename,
  uploadUrl,
  resultKey,
  onStoreMutated,
}) {
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);

  function handleDownload() {
    const a = document.createElement("a");
    a.href = templateUrl;
    a.download = templateFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  async function handleUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setStatus(null);
    try {
      const form = new FormData();
      form.append("file", file, file.name);
      const resp = await fetch(uploadUrl, { method: "POST", body: form });
      const body = await resp.json();
      if (body.error) {
        setStatus({ ok: false, msg: body.error });
      } else {
        const count = body[resultKey] ?? 0;
        const extras = Object.entries(body)
          .filter(([k]) => k !== resultKey && typeof body[k] === "number")
          .map(([k, v]) => `${k}: ${v}`)
          .join(" · ");
        setStatus({
          ok: true,
          msg: `Imported ${count} ${resultKey.replace("_", " ")}${extras ? "  ·  " + extras : ""}`,
        });
        onStoreMutated?.();
      }
    } catch (err) {
      setStatus({ ok: false, msg: err.message });
    } finally {
      setBusy(false);
      e.target.value = ""; // allow re-uploading the same file
    }
  }

  return (
    <section className="md-card">
      <div className="md-stack">
        <div className="md-stack-sm">
          <h3 className="md-headline-small">{title}</h3>
          <p className="md-body-medium md-on-surface-variant">{description}</p>
        </div>

        <div className="md-row">
          <button
            type="button"
            className="md-btn md-btn-outlined"
            onClick={handleDownload}
          >
            Download template
          </button>
          <label className="md-btn md-btn-tonal" style={{ cursor: busy ? "wait" : "pointer" }}>
            {busy ? "Uploading…" : "Upload filled xlsx"}
            <input
              type="file"
              accept=".xlsx"
              style={{ display: "none" }}
              disabled={busy}
              onChange={handleUpload}
            />
          </label>
        </div>

        {status && (
          <div
            className="md-card"
            style={{
              background: status.ok
                ? "var(--md-success-container)"
                : "var(--md-error-container)",
              padding: "var(--md-space-3) var(--md-space-4)",
            }}
          >
            <p
              className="md-body-small md-mono"
              style={{
                color: status.ok
                  ? "var(--md-on-success-container)"
                  : "var(--md-on-error-container)",
              }}
            >
              {status.ok ? "✔ " : "✘ "}
              {status.msg}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

export default function Upload({ onStoreMutated }) {
  return (
    <div className="md-stack-lg">
      <section className="md-stack-sm">
        <span className="md-eyebrow">Bulk import</span>
        <h3 className="md-headline-small">Excel templates</h3>
        <p className="md-body-large md-on-surface-variant" style={{ maxWidth: 680 }}>
          Download a template, fill it in using Excel/Numbers/Sheets, and upload
          it back. Uploads write directly to the shared SQLite store, so the
          Analyst and Investor views refresh immediately.
        </p>
      </section>

      <div className="md-grid md-grid-auto">
        <UploadCard
          title="Onboarding"
          description="Two-sheet workbook: Funds on sheet 1, Investments (deal ↔ fund, ownership %) on sheet 2. Use this to stand up a new portfolio shell."
          templateUrl="/api/admin/template/onboarding"
          templateFilename="fundlens_onboarding_template.xlsx"
          uploadUrl="/api/admin/upload/onboarding"
          resultKey="ownerships_added"
          onStoreMutated={onStoreMutated}
        />
        <UploadCard
          title="Cashflows"
          description="One sheet of dated transactions (Investment / Current Income / Disposition). Fund amounts are in USD millions — contributions go in as negative."
          templateUrl="/api/admin/template/cashflow"
          templateFilename="fundlens_cashflow_template.xlsx"
          uploadUrl="/api/admin/upload/cashflow"
          resultKey="cashflows_added"
          onStoreMutated={onStoreMutated}
        />
      </div>
    </div>
  );
}

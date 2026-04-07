// Plain-English benchmark labels for MOIC, IRR, and NAV movement used across
// the Investor portal. Ported verbatim from the old Gradio investor/ui.py.
//
// These thresholds are the one place where real estate PE domain expertise
// lives in the frontend. If the demo narrative wants "strong outperformance"
// to kick in at a different MOIC, tweak the numbers here and every fund card
// + NAV walk will update automatically.
//
// Metric availability (easy/medium/hard) mirrors what `submit_report` grades:
// easy grades only the bridge, medium adds MOIC, hard adds MOIC + IRR.

export const METRIC_AVAILABILITY = {
  moic: { easy: false, medium: true,  hard: true  },
  irr:  { easy: false, medium: false, hard: true  },
};

const AVAILABLE_FROM = { moic: "Medium", irr: "Hard" };

function notAvailable(metric, taskId) {
  if (!taskId) return "— (no scenario loaded)";
  return `— (available in ${AVAILABLE_FROM[metric] || "?"} mode and above)`;
}

export function moicLabel(moic, taskId) {
  if (!METRIC_AVAILABILITY.moic[taskId] || moic == null || moic <= 0) {
    return notAvailable("moic", taskId);
  }
  if (moic >= 2.5) return `${moic.toFixed(2)}x  ★ Strong outperformance`;
  if (moic >= 2.0) return `${moic.toFixed(2)}x  ✔ Good return`;
  if (moic >= 1.5) return `${moic.toFixed(2)}x  → Moderate return`;
  if (moic >= 1.0) return `${moic.toFixed(2)}x  ⚠ Capital returned, limited gain`;
  return `${moic.toFixed(2)}x  ✘ Capital loss`;
}

export function irrLabel(irr, taskId) {
  if (!METRIC_AVAILABILITY.irr[taskId] || irr == null || irr <= 0) {
    return notAvailable("irr", taskId);
  }
  const pct = irr * 100;
  if (pct >= 20) return `${pct.toFixed(1)}%  ★ Excellent annual return`;
  if (pct >= 12) return `${pct.toFixed(1)}%  ✔ Good annual return`;
  if (pct >= 8)  return `${pct.toFixed(1)}%  → In line with market`;
  if (pct >= 0)  return `${pct.toFixed(1)}%  ⚠ Below target`;
  return `${pct.toFixed(1)}%  ✘ Negative return`;
}

export function navChangeLabel(beg, end) {
  if (beg == null || end == null) return "—";
  if (beg === 0) return `—  →  $${end.toFixed(1)}M`;
  const change = end - beg;
  const pct    = (change / beg) * 100;
  const sign   = change >= 0 ? "+" : "";
  return `$${beg.toFixed(1)}M  →  $${end.toFixed(1)}M  (${sign}${pct.toFixed(1)}% this period)`;
}

// Mode banner copy -- same buckets the old portal showed.
export const MODE_META = {
  easy:    { label: "Easy Mode",    graded: "Graded: NAV Bridge only (8 line items)" },
  medium:  { label: "Medium Mode",  graded: "Graded: NAV Bridge + MOIC" },
  hard:    { label: "Hard Mode",    graded: "Graded: NAV Bridge + MOIC + IRR" },
};

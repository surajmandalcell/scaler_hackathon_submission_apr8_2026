// MD3 Navigation Rail. Vertical icon-rail on the left of the app shell with
// one item per persona. Inline SVG icons (24x24 stroke-1.75) keep the bundle
// free of an icon library while staying crisp at any zoom level.

const ICONS = {
  analyst: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 3v18h18" />
      <path d="M7 14l4-4 4 4 5-5" />
      <circle cx="7" cy="14" r="1.2" fill="currentColor" />
      <circle cx="11" cy="10" r="1.2" fill="currentColor" />
      <circle cx="15" cy="14" r="1.2" fill="currentColor" />
      <circle cx="20" cy="9" r="1.2" fill="currentColor" />
    </svg>
  ),
  admin: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 2.5l2.4 2.1 3.1-.6 1.3 2.9 2.7 1.6-.6 3.1L22 13.5l-1.1 3 .6 3.1-2.9 1.3-1.6 2.7-3.1-.6L12 25l-2.4-2.1-3.1.6-1.3-2.9-2.7-1.6.6-3.1L2 13.5l1.1-3-.6-3.1 2.9-1.3 1.6-2.7 3.1.6L12 2.5z" />
      <circle cx="12" cy="13" r="3.5" />
    </svg>
  ),
  investor: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="7" width="18" height="13" rx="2.5" />
      <path d="M8 7V5.5A2.5 2.5 0 0 1 10.5 3h3A2.5 2.5 0 0 1 16 5.5V7" />
      <path d="M3 12h18" />
      <circle cx="12" cy="15" r="1.4" fill="currentColor" />
    </svg>
  ),
  playground: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="3" y="4" width="18" height="16" rx="3" />
      <path d="M7 9l3 3-3 3" />
      <path d="M13 15h5" />
    </svg>
  ),
  docs: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 3.5h11l3 3v14a1.5 1.5 0 0 1-1.5 1.5h-12.5a1 1 0 0 1-1-1v-16a1 1 0 0 1 1-1z" />
      <path d="M16 3.5V7h3" />
      <path d="M8 12h8" />
      <path d="M8 16h8" />
      <path d="M8 8h4" />
    </svg>
  ),
};

export default function NavRail({ items, current, onChange }) {
  return (
    <aside className="md-rail" aria-label="Primary navigation">
      <div className="md-rail-brand">
        <span className="app-logo-dot" aria-hidden="true">F</span>
      </div>

      <div className="md-rail-list" role="tablist" aria-orientation="vertical">
        {items.map((item) => {
          const isActive = current === item.id;
          return (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-label={item.label}
              className={`md-rail-item ${isActive ? "is-active" : ""}`}
              onClick={() => onChange(item.id)}
            >
              <span className="md-rail-icon">{ICONS[item.id]}</span>
              <span className="md-rail-label">{item.label}</span>
            </button>
          );
        })}
      </div>

      <div className="md-rail-spacer" />
    </aside>
  );
}

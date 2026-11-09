import { Link } from "react-router";

const icons = {
  overview: (
    <>
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
    </>
  ),
  products: (
    <>
      <path d="m4 7 8-4 8 4v10l-8 4-8-4V7Z" />
      <path d="m4 7 8 4 8-4M12 11v10" />
    </>
  ),
  inventory: <path d="M3 7h18v14H3zM6 3h12v4M8 12h8" />,
  customers: (
    <>
      <circle cx="9" cy="8" r="3" />
      <circle cx="17" cy="9" r="2.5" />
      <path d="M3 20c.5-4 2.5-6 6-6s5.5 2 6 6M15 15c3-.5 5 .9 6 4" />
    </>
  ),
  orders: (
    <>
      <path d="M5 3h14v18H5zM8 8h8M8 12h8M8 16h4" />
    </>
  ),
  activity: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  team: (
    <>
      <circle cx="8" cy="8" r="3" />
      <circle cx="17" cy="9" r="2.5" />
      <path d="M2 21c.5-4.5 2.5-7 6-7s5.5 2.5 6 7M14 15c4-.5 6 1.5 7 5" />
    </>
  ),
  invite: (
    <>
      <path d="M3 5h13v13H3zM3 6l6.5 6L16 6M19 11v8M15 15h8" />
    </>
  ),
  settings: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 10h18M7 15h3" />
    </>
  ),
  credit: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path
        d="M19 13.5v-3l-2-.8-.8-1.9.8-2-2.1-2.1-2 .8-1.9-.8-.8-2h-3l-.8 2-1.9.8-2-.8L.4 5.8l.8 2-.8 1.9-2 .8v3l2 .8.8 1.9-.8 2 2.1 2.1 2-.8 1.9.8.8 2h3l.8-2 1.9-.8 2 .8 2.1-2.1-.8-2 .8-1.9 2-.8Z"
        transform="translate(2)"
      />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m16 16 5 5" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  chevron: <path d="m8 10 4 4 4-4" />,
  sync: (
    <>
      <path d="M20 7h-5V2" />
      <path d="M19 7a8 8 0 1 0 1 8" />
    </>
  ),
  alert: (
    <>
      <path d="M12 3 2.5 20h19L12 3Z" />
      <path d="M12 9v5M12 17h.01" />
    </>
  ),
};

export function Icon({ name }) {
  return (
    <span className={`ui-icon icon-${name}`} aria-hidden="true">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {icons[name] || icons.overview}
      </svg>
    </span>
  );
}

export function PageHeader({ eyebrow, title, description, action }) {
  return (
    <header className="page-header">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action && <div className="page-header-action">{action}</div>}
    </header>
  );
}

export function Status({ children, tone }) {
  return (
    <span className={`status ${tone || String(children).toLowerCase()}`}>
      {children}
    </span>
  );
}

export function Search({ value, onChange, placeholder = "Search" }) {
  return (
    <label className="search-field">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}

export function Notice({ children, tone = "info" }) {
  return <div className={`notice ${tone}`}>{children}</div>;
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}

export function Pagination({ page = 1, pages = 1, onChange }) {
  return (
    <div className="pagination">
      <button disabled={page <= 1} onClick={() => onChange?.(page - 1)}>
        ←
      </button>
      <span>
        {page} / {pages}
      </span>
      <button disabled={page >= pages} onClick={() => onChange?.(page + 1)}>
        →
      </button>
    </div>
  );
}

export function ActionLink({ to, title, copy, action }) {
  return (
    <Link to={to} className="action-link">
      <strong>{title}</strong>
      <span>{copy}</span>
      {action}
    </Link>
  );
}

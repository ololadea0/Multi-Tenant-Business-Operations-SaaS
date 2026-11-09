import { Link } from "react-router"

export function Logo({ light = false }) {
  return (
    <Link
      to="/"
      className={`logo ${light ? "text-paper" : "text-ink"}`}
      aria-label="Daymark home"
    >
      <svg viewBox="0 0 32 32" aria-hidden="true">
        <path
          d="M6 5h10c6.1 0 10 3.8 10 11s-3.9 11-10 11H6V5Z"
          fill="currentColor"
        />
        <path
          d="M12 10h3.5c3 0 4.7 2.1 4.7 6s-1.7 6-4.7 6H12V10Z"
          fill="var(--paper)"
        />
        <path d="M24 6.5 27.5 3 29 4.5 25.5 8 24 6.5Z" fill="var(--accent)" />
      </svg>
      <span>Daymark</span>
    </Link>
  )
}

export function Arrow({ diagonal = false }) {
  return (
    <svg className="arrow" viewBox="0 0 18 18" aria-hidden="true">
      {diagonal ? (
        <path d="M4 14 14 4m-8 0h8v8" />
      ) : (
        <path d="M3 9h11m-4-4 4 4-4 4" />
      )}
    </svg>
  )
}

export const MarkIcon = ({ name }) => {
  const paths = {
    products: (
      <>
        <path d="M5 8.5 12 5l7 3.5v8L12 20l-7-3.5v-8Z" />
        <path d="m5 8.5 7 3.5 7-3.5M12 12v8" />
      </>
    ),
    inventory: (
      <>
        <path d="M4 7h16v12H4zM7 4h10v3" />
        <path d="M8 12h8" />
      </>
    ),
    customers: (
      <>
        <circle cx="9" cy="9" r="3" />
        <circle cx="17" cy="10" r="2.5" />
        <path d="M3.5 19c.7-3.2 2.5-4.7 5.5-4.7s4.8 1.5 5.5 4.7M14 15.5c3.4-.8 5.6.4 6.5 3.5" />
      </>
    ),
    orders: (
      <>
        <path d="M6 4h12v16H6zM9 8h6M9 12h6M9 16h3" />
      </>
    ),
    insights: (
      <>
        <path d="M5 19V9M12 19V5M19 19v-7" />
      </>
    ),
    team: (
      <>
        <circle cx="12" cy="8" r="3" />
        <path d="M5 20c.6-4.1 2.9-6 7-6s6.4 1.9 7 6" />
      </>
    ),
  }
  return (
    <svg className="mark-icon" viewBox="0 0 24 24" aria-hidden="true">
      {paths[name]}
    </svg>
  )
}

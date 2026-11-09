import { Component, useEffect } from "react"
import { Link, isRouteErrorResponse, useNavigate, useRouteError } from "react-router"

function errorCopy(error) {
  if (isRouteErrorResponse(error)) {
    if (error.status === 401) return ["Sign in required", "Please sign in to continue to this workspace."]
    if (error.status === 403) return ["Access unavailable", "You do not have permission to view this page."]
    if (error.status === 404) return ["Page not found", "That page is not part of this Daymark workspace."]
    if (error.status >= 500) return ["Daymark is having trouble", "We could not load this page right now. Please try again."]
  }
  return ["Something went wrong", "We could not load this page. Please try again or return home."]
}

export function RouteErrorPage() {
  const error = useRouteError()
  const navigate = useNavigate()
  useEffect(() => { if (import.meta.env.DEV) console.error("Daymark route error", error) }, [error])
  const [title, message] = errorCopy(error)
  const status = isRouteErrorResponse(error) ? error.status : 500
  return <main className="daymark-error-page"><div className="daymark-error-card"><span className="eyebrow">DAYMARK / {status}</span><h1>{title}</h1><p>{message}</p><div className="daymark-error-actions"><button className="app-btn primary" onClick={() => window.location.reload()}>Retry</button><button className="app-btn secondary" onClick={() => navigate(-1)}>Go back</button><Link className="app-btn secondary" to="/">Home</Link></div></div></main>
}

export function NotFoundPage() { return <main className="daymark-error-page"><div className="daymark-error-card"><span className="eyebrow">DAYMARK / 404</span><h1>Page not found</h1><p>This page is not on the day’s agenda.</p><Link className="app-btn primary" to="/">Return home</Link></div></main> }

export class ReactErrorBoundary extends Component {
  state = { hasError: false }
  static getDerivedStateFromError() { return { hasError: true } }
  componentDidCatch(error, info) { if (import.meta.env.DEV) console.error("Daymark render error", error, info) }
  render() { if (!this.state.hasError) return this.props.children; return <main className="daymark-error-page"><div className="daymark-error-card"><span className="eyebrow">DAYMARK / ERROR</span><h1>Something went wrong</h1><p>Daymark could not display this screen. Please retry or return home.</p><button className="app-btn primary" onClick={() => window.location.reload()}>Retry</button></div></main> }
}

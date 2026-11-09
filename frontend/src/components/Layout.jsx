import { useEffect, useState } from "react"
import { Link, NavLink, Outlet, useLocation } from "react-router"
import { Arrow, Logo } from "./Brand"

const nav = [
  ["Product", "/features"],
  ["Solutions", "/solutions"],
  ["About", "/about"],
  ["Contact us", "/contact"],
]

export function Header() {
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()
  useEffect(() => setOpen(false), [pathname])
  return (
    <header className="site-header">
      <div className="nav-shell">
        <Logo />
        <nav
          className={`nav-links ${open ? "is-open" : ""}`}
          aria-label="Main navigation"
        >
          {nav.map(([label, path]) => (
            <NavLink key={path} to={path}>
              {label}
            </NavLink>
          ))}
          <Link className="mobile-login" to="/login">
            Log in
          </Link>
          <Link className="button button-dark mobile-cta" to="/register">
            Get started <Arrow />
          </Link>
        </nav>
        <div className="nav-actions">
          <Link to="/login">Log in</Link>
          <Link className="button button-dark button-sm" to="/register">
            Get started <Arrow />
          </Link>
        </div>
        <button
          className="menu-button"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
          aria-expanded={open}
        >
          <span />
          <span />
        </button>
      </div>
    </header>
  )
}

export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-main">
        <div className="footer-brand">
          <Logo light />
          <p>
            One clear workspace for the work that keeps your business moving.
          </p>
        </div>
        <div className="footer-links">
          <div>
            <b>Platform</b>
            <Link to="/features">Features</Link>
            <Link to="/solutions">Solutions</Link>
            <Link to="/register">Get started</Link>
          </div>
          <div>
            <b>Company</b>
            <Link to="/about">About</Link>
            <Link to="/contact">Contact</Link>
            <a href="mailto:hello@daymark.example">hello@daymark.example</a>
          </div>
          <div>
            <b>Legal</b>
            <Link to="/privacy">Privacy</Link>
            <Link to="/terms">Terms</Link>
            <Link to="/login">Log in</Link>
          </div>
        </div>
      </div>
      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} Daymark. All rights reserved.</span>
        <span className="mono">OPERATIONS / IN VIEW</span>
      </div>
    </footer>
  )
}

export function PublicLayout() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return (
    <>
      <Header />
      <Outlet />
      <Footer />
    </>
  )
}

export function AuthLayout() {
  return (
    <main className="auth-layout">
      <section className="auth-panel">
        <div className="auth-brand">
          <Logo light />
        </div>
        <div className="auth-message">
          <span className="eyebrow text-sage">A CLEARER WORKING DAY</span>
          <h2>
            Know what’s moving.
            <br />
            Know what needs you.
          </h2>
          <p>
            Products, stock, customers and orders—connected in one calm
            workspace.
          </p>
        </div>
        <div className="auth-orbit" aria-hidden="true">
          <i />
          <i />
          <i />
          <span>DM</span>
        </div>
      </section>
      <section className="auth-form-side">
        <Outlet />
      </section>
    </main>
  )
}

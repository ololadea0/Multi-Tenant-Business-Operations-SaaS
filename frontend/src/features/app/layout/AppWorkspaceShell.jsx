import { Link, NavLink } from "react-router";
import { Icon } from "../../../app/application/Ui";

export function WorkspaceShell({
  collapsed,
  setCollapsed,
  mobile,
  setMobile,
  orgOpen,
  setOrgOpen,
  organizationName,
  organizationRole,
  userName,
  userEmail,
  online,
  syncMessage,
  maintenanceBanner,
  base,
  segment,
  names,
  mainNavContent,
  manageNavContent,
  orgOptions,
  navigate,
  organizationId,
  children,
}) {
  return (
    <div
      className={`application ${collapsed ? "sidebar-compact" : ""} ${
        mobile ? "mobile-nav-open" : ""
      }`}
    >
      <aside className="app-sidebar">
        <div className="app-logo">
          <Link to="/">
            <svg viewBox="0 0 32 32">
              <path
                d="M6 5h10c6.1 0 10 3.8 10 11s-3.9 11-10 11H6V5Z"
                fill="currentColor"
              />
              <path
                d="M12 10h3.5c3 0 4.7 2.1 4.7 6s-1.7 6-4.7 6H12V10Z"
                fill="#17211e"
              />
              <path d="M24 6.5 27.5 3 29 4.5 25.5 8 24 6.5Z" fill="#ff5c35" />
            </svg>
            <span>Daymark</span>
          </Link>
          <button
            onClick={() => setCollapsed(!collapsed)}
            aria-label="Collapse sidebar"
          >
            ‹
          </button>
        </div>

        <div className="org-switch">
          <button onClick={() => setOrgOpen(!orgOpen)}>
            <span className="org-avatar">
              {organizationName.slice(0, 2).toUpperCase()}
            </span>
            <span>
              <b>{organizationName}</b>
              <small>{organizationRole} workspace</small>
            </span>
            <Icon name="chevron" />
          </button>

          {orgOpen && (
            <div className="org-menu">
              <button
                onClick={() => {
                  navigate(`/app/${organizationId}/dashboard`);
                  setOrgOpen(false);
                }}
              >
                <i>{organizationName.slice(0, 2).toUpperCase()}</i>
                <span>
                  <b>{organizationName}</b>
                  <small>{organizationRole}</small>
                </span>
                <em>✓</em>
              </button>
              {orgOptions.map((item) => (
                <button
                  key={item.id}
                  onClick={() => {
                    navigate(`/app/${item.id}/dashboard`);
                    setOrgOpen(false);
                  }}
                >
                  <i>{item.name.slice(0, 2).toUpperCase()}</i>
                  <span>
                    <b>{item.name}</b>
                    <small>{item.role}</small>
                  </span>
                </button>
              ))}
              <Link to="/app/organizations">View all organizations</Link>
            </div>
          )}
        </div>

        <nav className="app-nav">
          <small>WORKSPACE</small>
          {mainNavContent}
          <small>MANAGE</small>
          {manageNavContent}
        </nav>

        <div className="app-side-bottom">
          <NavLink to={`${base}/settings`}>
            <Icon name="settings" />
            <span>Settings</span>
          </NavLink>
          <NavLink to={`${base}/settings/billing`}>
            <Icon name="credit" />
            <span>Billing</span>
          </NavLink>
          <button className={`side-sync ${online ? "" : "offline"}`}>
            <i />
            <span>
              <b>{online ? "All changes synced" : "Working offline"}</b>
              <small>
                {syncMessage ||
                  (online ? "Backend reachable" : "Using saved data")}
              </small>
            </span>
          </button>
          <NavLink to={`${base}/profile`} className="side-profile">
            <span className="profile-avatar">AM</span>
            <span>
              <b>{userName}</b>
              <small>{userEmail || ""}</small>
            </span>
            <Icon name="chevron" />
          </NavLink>
        </div>
      </aside>

      {mobile && (
        <button
          className="app-scrim"
          onClick={() => setMobile(false)}
          aria-label="Close menu"
        />
      )}

      <div className="app-main">
        <header className="app-topbar">
          <button className="mobile-app-menu" onClick={() => setMobile(true)}>
            <Icon name="menu" />
          </button>
          <div className="app-crumb">
            <span>{organizationName}</span>
            <i>/</i>
            <b>{names[segment] || "Details"}</b>
          </div>
          <div className="top-actions">
            <Link
              className={`top-sync ${online ? "" : "offline"}`}
              to={`${base}/sync`}
            >
              <i />
              {online ? "Synced" : "3 pending"}
            </Link>
            <input
              className="global-search"
              placeholder="Search products"
              onKeyDown={(event) => {
                if (event.key === "Enter" && event.currentTarget.value.trim()) {
                  navigate(
                    `${base}/products?search=${encodeURIComponent(event.currentTarget.value.trim())}`,
                  );
                }
              }}
            />
            <button className="global-search" hidden>
              <Icon name="search" />
              <span>Search</span>
              <kbd>⌘ K</kbd>
            </button>
            <button className="top-avatar">AM</button>
          </div>
        </header>

        {!online && (
          <div className="offline-bar">
            <b>You’re offline.</b> Viewing data saved on this device. Supported
            changes will sync when your connection returns.
            <Link to={`${base}/sync`}>View pending actions</Link>
          </div>
        )}

        {maintenanceBanner && (
          <div
            style={{
              background: "#111917",
              color: "#f5f6f2",
              padding: "10px 16px",
              borderBottom: "1px solid rgba(255,255,255,0.08)",
              overflow: "hidden",
              whiteSpace: "nowrap",
            }}
          >
            <div
              style={{
                display: "inline-block",
                minWidth: "100%",
                animation: "maintenanceScroll 18s linear infinite",
              }}
            >
              <span style={{ marginRight: "30px", fontWeight: 800 }}>
                {maintenanceBanner.title}
              </span>
              <span style={{ opacity: 0.9 }}>{maintenanceBanner.message}</span>
            </div>
            <style>{`
              @keyframes maintenanceScroll {
                0% { transform: translateX(0%); }
                100% { transform: translateX(-15%); }
              }
            `}</style>
          </div>
        )}

        <div className="app-content">{children}</div>
      </div>
    </div>
  );
}

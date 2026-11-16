import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { Icon } from "../../app/application/Ui";
import { useMeQuery } from "../../app/store/api";
import { organizationCleared, signedOut } from "../../app/store/slices";

const adminSections = [
  {
    title: "OVERVIEW",
    items: [
      { label: "Dashboard", path: "/admin", icon: "overview", exact: true },
    ],
  },
  {
    title: "PLATFORM MANAGEMENT",
    items: [
      { label: "Businesses", path: "/admin/businesses", icon: "products" },
      { label: "Users", path: "/admin/users", icon: "customers" },
      { label: "Subscriptions", path: "/admin/subscriptions", icon: "orders" },
      { label: "Payments", path: "/admin/payments", icon: "inventory" },
      { label: "Plans & Pricing", path: "/admin/plans", icon: "invite" },
    ],
  },
  {
    title: "COMMUNICATION",
    items: [
      { label: "Email Centre", path: "/admin/email-centre", icon: "mail" },
      {
        label: "Announcements",
        path: "/admin/announcements",
        icon: "activity",
      },
    ],
  },
  {
    title: "INSIGHTS & SECURITY",
    items: [
      { label: "Analytics", path: "/admin/analytics", icon: "activity" },
      { label: "Audit Logs", path: "/admin/audit-logs", icon: "team" },
      { label: "System Health", path: "/admin/health", icon: "sync" },
    ],
  },
  {
    title: "CONFIGURATION",
    items: [
      { label: "Platform Settings", path: "/admin/settings", icon: "settings" },
    ],
  },
];

const titles = {
  businesses: "Businesses",
  users: "Users",
  subscriptions: "Subscriptions",
  payments: "Payments",
  plans: "Plans & Pricing",
  "email-centre": "Email Centre",
  "email-compose": "Compose Email",
  "email-templates": "Email Templates",
  "email-automation": "Automated Emails",
  "email-history": "Email History",
  analytics: "Analytics",
  settings: "Platform Settings",
  "audit-logs": "Audit Logs",
  health: "System Health",
  announcements: "Announcements",
};

export function AdminLayout() {
  const { data: currentUser } = useMeQuery();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState({
    OVERVIEW: true,
    "PLATFORM MANAGEMENT": true,
    COMMUNICATION: true,
    "INSIGHTS & SECURITY": true,
    CONFIGURATION: true,
  });
  const { pathname } = useLocation();

  useEffect(() => {
    setOpen(false);
    window.scrollTo(0, 0);
  }, [pathname]);

  const segment = pathname.split("/")[2] || "";
  const adminName = currentUser?.full_name || currentUser?.email || "Platform administrator";
  const adminInitials = adminName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
  const adminRole = currentUser?.platform_role
    ? currentUser.platform_role.replaceAll("_", " ")
    : "Platform administrator";

  const toggleSection = (section) => {
    setExpanded((current) => ({
      ...current,
      [section]: !current[section],
    }));
  };

  return (
    <>
      <style>{`
        .admin-environment {
          display: flex;
          height: 100vh;
          overflow: hidden;
          background: #f5f6f2;
          color: #111917;
        }

        .admin-sidebar {
          position: sticky;
          top: 0;
          width: 284px;
          height: 100vh;
          background: #111917;
          color: #f5f6f2;
          padding: 20px 14px 18px;
          display: flex;
          flex-direction: column;
          gap: 18px;
          border-right: 1px solid rgba(255,255,255,0.08);
          flex-shrink: 0;
          overflow-y: auto;
          -ms-overflow-style: none;
          scrollbar-width: none;
        }

        .admin-sidebar::-webkit-scrollbar {
          display: none;
        }

        .admin-brand {
          display: flex;
          align-items: center;
          gap: 12px;
          color: #f5f6f2;
          padding: 6px 8px 16px;
          text-decoration: none;
        }

        .admin-brand b { display: block; font-size: 1.05rem; }
        .admin-brand small { opacity: 0.8; font-size: 11px; }

        .admin-nav-groups {
          display: flex;
          flex-direction: column;
          gap: 14px;
          overflow-y: auto;
          padding-right: 2px;
          -ms-overflow-style: none;
          scrollbar-width: none;
        }

        .admin-nav-groups::-webkit-scrollbar {
          display: none;
        }

        .admin-nav-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .admin-nav-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          padding: 8px 10px 6px;
          color: rgba(223, 229, 223, 0.7);
          font-size: 11px;
          letter-spacing: 0.12em;
          font-weight: 700;
          text-transform: uppercase;
          user-select: none;
        }

        .admin-nav-header button {
          background: transparent;
          border: 0;
          color: inherit;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 18px;
          height: 18px;
          padding: 0;
          cursor: pointer;
        }

        .admin-nav-links {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .admin-nav-links a {
          display: flex;
          align-items: center;
          gap: 10px;
          width: 100%;
          padding: 9px 10px;
          border-radius: 10px;
          color: #dfe5df;
          text-decoration: none;
          font-weight: 600;
          transition: background 0.18s ease, color 0.18s ease, transform 0.18s ease;
        }

        .admin-nav-links a:hover {
          background: rgba(255,255,255,0.04);
        }

        .admin-nav-links a.active {
          background: #f5f6f2;
          color: #111917;
        }

        .admin-nav-links a .ui-icon {
          width: 16px;
          height: 16px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }

        .admin-nav-links a .ui-icon svg {
          width: 16px;
          height: 16px;
        }

        .admin-side-foot {
          margin-top: auto;
          border-top: 1px solid rgba(255,255,255,0.12);
          padding-top: 18px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .admin-profile {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 8px 6px;
        }

        .admin-profile-badge {
          width: 36px;
          height: 36px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          background: #ff5c35;
          color: #111917;
          font-weight: 800;
        }

        .admin-main {
          flex: 1;
          display: flex;
          flex-direction: column;
          min-width: 0;
          height: 100vh;
          overflow: hidden;
        }

        .admin-topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
          padding: 18px 24px;
          border-bottom: 1px solid rgba(17,25,23,0.08);
          background: rgba(255,255,255,0.6);
          backdrop-filter: blur(10px);
        }

        .admin-menu {
          display: none !important;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          height: 40px;
          border: 1px solid rgba(17,25,23,0.1);
          border-radius: 12px;
          background: #fff;
          color: #111917;
          cursor: pointer;
        }

        .admin-content {
          flex: 1;
          padding: 28px 24px 48px;
          overflow-y: auto;
          overflow-x: hidden;
        }

        @media (max-width: 980px) {
          .admin-environment {
            display: block;
          }

          .admin-sidebar {
            position: fixed;
            inset: 0 auto 0 0;
            width: min(86vw, 320px);
            transform: translateX(-100%);
            transition: transform 0.2s ease;
            z-index: 20;
            box-shadow: 12px 0 30px rgba(17,25,23,0.16);
          }

          .admin-nav-open .admin-sidebar {
            transform: translateX(0);
          }

          .admin-scrim {
            position: fixed;
            inset: 0;
            background: rgba(17,25,23,0.4);
            border: 0;
            z-index: 10;
          }

          .admin-topbar {
            padding: 16px 18px;
          }

          .admin-menu {
            display: inline-flex !important;
          }

          .admin-content {
            padding: 20px 18px 36px;
          }
        }
      `}</style>

      <div
        className={`admin-environment ${open ? "admin-nav-open" : ""}`}
        style={{
          display: "flex",
          minHeight: "100vh",
          background: "#f5f6f2",
          color: "#111917",
        }}
      >
        <aside className="admin-sidebar">
          <Link className="admin-brand" to="/admin">
            <svg
              viewBox="0 0 32 32"
              style={{ width: "28px", height: "28px", flex: "none" }}
            >
              <path
                d="M6 5h10c6.1 0 10 3.8 10 11s-3.9 11-10 11H6V5Z"
                fill="currentColor"
              />
              <path
                d="M12 10h3.5c3 0 4.7 2.1 4.7 6s-1.7 6-4.7 6H12V10Z"
                fill="#111917"
              />
              <path d="M24 6.5 27.5 3 29 4.5 25.5 8 24 6.5Z" fill="#ff5c35" />
            </svg>
            <span
              style={{
                display: "flex",
                flexDirection: "column",
                lineHeight: 1.1,
              }}
            >
              <b>Daymark Admin</b>
              <small>Platform administration</small>
            </span>
          </Link>

          <nav
            className="admin-nav-groups"
            aria-label="Platform admin navigation"
          >
            {adminSections.map((section) => {
              const isExpanded = expanded[section.title];

              return (
                <div className="admin-nav-group" key={section.title}>
                  <div className="admin-nav-header">
                    <span>{section.title}</span>
                    <button
                      type="button"
                      aria-label={
                        isExpanded
                          ? `Hide ${section.title}`
                          : `Show ${section.title}`
                      }
                      onClick={() => toggleSection(section.title)}
                      style={{
                        transform: isExpanded
                          ? "rotate(0deg)"
                          : "rotate(-90deg)",
                        transition: "transform 0.2s ease",
                      }}
                    >
                      <Icon name="chevron" />
                    </button>
                  </div>

                  {isExpanded && (
                    <div className="admin-nav-links">
                      {section.items.map((item) => (
                        <NavLink
                          key={item.path}
                          end={Boolean(item.exact)}
                          to={item.path}
                          className={({ isActive }) =>
                            isActive ? "active" : ""
                          }
                        >
                          <Icon name={item.icon} />
                          <span>{item.label}</span>
                        </NavLink>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>

          <div className="admin-side-foot">
            <div className="admin-profile">
              <span className="admin-profile-badge">{adminInitials}</span>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  lineHeight: 1.2,
                }}
              >
                <b style={{ fontSize: "0.95rem" }}>{adminName}</b>
                <small style={{ opacity: 0.76 }}>{adminRole}</small>
              </div>
            </div>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "10px",
                padding: "0 6px",
              }}
            >
              <button
                type="button"
                onClick={() => {
                  localStorage.removeItem("daymark.accessToken");
                  dispatch(signedOut());
                  dispatch(organizationCleared());
                  navigate("/login", { replace: true });
                }}
                style={{
                  background: "transparent",
                  border: "1px solid rgba(255,255,255,0.12)",
                  color: "#f5f6f2",
                  borderRadius: "10px",
                  padding: "10px 12px",
                  textAlign: "left",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Log out
              </button>
              <Link
                to="/"
                style={{
                  color: "#dfe5df",
                  opacity: 0.9,
                  fontWeight: 600,
                  textDecoration: "none",
                }}
              >
                ← Return to Daymark site
              </Link>
            </div>
          </div>
        </aside>

        {open && (
          <button
            className="admin-scrim"
            onClick={() => setOpen(false)}
            aria-label="Close navigation"
          />
        )}

        <div className="admin-main">
          <header className="admin-topbar">
            <button
              className="admin-menu"
              onClick={() => setOpen(true)}
              aria-label="Open navigation"
            >
              <Icon name="menu" />
            </button>

            <div
              style={{
                display: "flex",
                flexDirection: "column",
                lineHeight: 1.15,
              }}
            >
              <span
                style={{
                  fontSize: "11px",
                  letterSpacing: "0.12em",
                  color: "#66706c",
                  fontWeight: 700,
                }}
              >
                PLATFORM
              </span>
              <b style={{ fontSize: "1.15rem" }}>
                {titles[segment] || "Overview"}
              </b>
            </div>

            <div
              className="admin-top-actions"
              style={{
                marginLeft: "auto",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                flexWrap: "wrap",
              }}
            >
              <button
                type="button"
                aria-label="Search businesses"
                title="Search businesses"
                onClick={() => navigate("/admin/businesses")}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "40px",
                  height: "40px",
                  border: "1px solid rgba(17,25,23,0.1)",
                  borderRadius: "50%",
                  background: "#fff",
                  color: "#111917",
                  cursor: "pointer",
                }}
              >
                <Icon name="search" />
              </button>
              <Link
                to="/admin/health"
                className="system-health"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  background: "#eaf9ee",
                  color: "#0d6c3d",
                  borderRadius: "999px",
                  padding: "9px 12px",
                  fontWeight: 700,
                }}
              >
                <i
                  style={{
                    width: "8px",
                    height: "8px",
                    display: "inline-block",
                    background: "#2bb673",
                    borderRadius: "50%",
                  }}
                />
                All systems operational
              </Link>
              <button
                className="top-avatar"
                type="button"
                onClick={() => navigate("/admin/settings")}
                style={{
                  width: "42px",
                  height: "42px",
                  borderRadius: "50%",
                  border: "0",
                  background: "#111917",
                  color: "#f5f6f2",
                  fontWeight: 800,
                  cursor: "pointer",
                }}
              >
                {adminInitials}
              </button>
            </div>
          </header>

          <div className="admin-content">
            <Outlet />
          </div>
        </div>
      </div>
    </>
  );
}

import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
  useParams,
} from "react-router";
import { Icon } from "./Ui";
import { useDispatch, useSelector } from "react-redux";
import { organizationSelected } from "../store/slices";
import {
  useCreateOrganizationMutation,
  useOrganizationsQuery,
  useMeQuery,
} from "../store/api";

const roleLabel = (role) =>
  String(role || "")
    .toLowerCase()
    .replace(/(^|\s)([a-z])/g, (m, s, ch) => s + ch.toUpperCase());

const mainNav = [
  ["Overview", "dashboard", "overview"],
  ["Products", "products", "products"],
  ["Inventory", "inventory", "inventory"],
  ["Customers", "customers", "customers"],
  ["Orders", "orders", "orders"],
];
const manageNav = [
  ["Activity", "activity", "activity"],
  ["Team", "team", "team"],
  ["Invitations", "invitations", "invite"],
];
const names = {
  dashboard: "Overview",
  products: "Products",
  inventory: "Inventory",
  customers: "Customers",
  orders: "Orders",
  activity: "Activity",
  team: "Team",
  invitations: "Invitations",
  settings: "Organization settings",
  profile: "Your profile",
  sync: "Sync centre",
  billing: "Billing",
};

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobile, setMobile] = useState(false);
  const [orgOpen, setOrgOpen] = useState(false);
  const { organizationId } = useParams();
  const dispatch = useDispatch();
  const online = useSelector((state) =>
    ["online", "synchronized"].includes(state.sync.state),
  );
  const syncMessage = useSelector((state) => state.sync.message);
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { data: organizations = [] } = useOrganizationsQuery();
  const { data: user } = useMeQuery();
  const organization = organizations.find(
    (item) => String(item.id) === String(organizationId),
  );
  const organizationName = organization?.name || "Organization";
  const organizationRole = organization?.role
    ? roleLabel(organization.role)
    : "Member";
  const userName = user?.full_name || "there";
  const initials = userName
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  const orgOptions = organizations.filter(
    (item) => String(item.id) !== String(organizationId),
  );
  useEffect(() => {
    setMobile(false);
    window.scrollTo(0, 0);
  }, [pathname]);
  useEffect(() => {
    dispatch(organizationSelected(organizationId));
  }, [dispatch, organizationId]);
  const segment = pathname.split("/").filter(Boolean)[2] || "dashboard";
  const base = `/app/${organizationId}`;
  const navItems = (items) =>
    items.map(([label, path, icon]) => (
      <NavLink key={path} to={`${base}/${path}`} aria-label={label}>
        <Icon name={icon} />
        <span>{label}</span>
      </NavLink>
    ));
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
                    <small>{roleLabel(item.role)}</small>
                  </span>
                </button>
              ))}
              <Link to="/app/organizations">View all organizations</Link>
            </div>
          )}
        </div>
        <nav className="app-nav">
          <small>WORKSPACE</small>
          {navItems(mainNav)}
          <small>MANAGE</small>
          {navItems(manageNav)}
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
              <small>{user?.email || ""}</small>
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
                if (event.key === "Enter" && event.currentTarget.value.trim())
                  navigate(
                    `${base}/products?search=${encodeURIComponent(event.currentTarget.value.trim())}`,
                  );
              }}
            />
            {/* Search submits to the organization product catalogue. */}
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
        <div className="app-content">
          <Outlet context={{ online }} />
        </div>
      </div>
    </div>
  );
}

function LegacyOrganizations() {
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();
  const { data: organizations = [], isLoading } = useOrganizationsQuery();
  const [createOrganization] = useCreateOrganizationMutation();
  async function submitOrganization(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const name = form.get("name");
    const email = form.get("email");
    const organization = await createOrganization({ name, email }).unwrap();
    navigate(`/app/${organization.id}/dashboard`);
  }
  return (
    <main className="org-select-page">
      <Link className="app-logo standalone" to="/">
        <svg viewBox="0 0 32 32">
          <path
            d="M6 5h10c6.1 0 10 3.8 10 11s-3.9 11-10 11H6V5Z"
            fill="currentColor"
          />
          <path
            d="M12 10h3.5c3 0 4.7 2.1 4.7 6s-1.7 6-4.7 6H12V10Z"
            fill="var(--paper)"
          />
        </svg>
        <span>Daymark</span>
      </Link>
      <section>
        <span className="mono">YOUR WORKSPACES</span>
        <h1>
          {creating ? "Create an organization." : "Choose an organization."}
        </h1>
        <p>
          {creating
            ? "Set up the separate workspace your team will use."
            : "Each workspace keeps its business data and team access separate."}
        </p>
        {creating ? (
          <form className="create-org-form" onSubmit={submitOrganization}>
            <label>
              Organization name
              <input
                name="name"
                required
                placeholder="Your business name"
                autoFocus
              />
            </label>
            <label>
              Business email <em>Optional</em>
              <input
                type="email"
                name="email"
                placeholder="hello@company.com"
              />
            </label>
            <div>
              <button
                type="button"
                className="app-btn secondary"
                onClick={() => setCreating(false)}
              >
                Cancel
              </button>
              <button className="app-btn primary">Create workspace</button>
            </div>
          </form>
        ) : (
          <>
            <div className="org-list">
              {isLoading && <p>Loading workspaces…</p>}
              {organizations.map((organization) => (
                <Link
                  key={organization.id}
                  to={`/app/${organization.id}/dashboard`}
                >
                  <i>{organization.name.slice(0, 2).toUpperCase()}</i>
                  <span>
                    <b>{organization.name}</b>
                    <small>{organization.role}</small>
                  </span>
                  <em>Open workspace →</em>
                </Link>
              ))}
              {!isLoading && !organizations.length && (
                <p>No organizations found.</p>
              )}
            </div>
            <button
              className="app-btn secondary"
              onClick={() => setCreating(true)}
            >
              + Create organization
            </button>
          </>
        )}
      </section>
    </main>
  );
}

export function Organizations() {
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();
  const {
    data: organizations = [],
    isLoading,
    error,
  } = useOrganizationsQuery();
  const [createOrganization, createState] = useCreateOrganizationMutation();
  async function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const name = form.get("name");
    const email = form.get("email");
    try {
      const organization = await createOrganization({ name, email }).unwrap();
      navigate(`/app/${organization.id}/dashboard`);
    } catch {}
  }
  return (
    <main className="org-select-page">
      <Link className="app-logo standalone" to="/">
        <span>Daymark</span>
      </Link>
      <section>
        <span className="mono">YOUR WORKSPACES</span>
        <h1>
          {creating ? "Create an organization." : "Choose an organization."}
        </h1>
        <p>
          {creating
            ? "Set up the separate workspace your team will use."
            : "Each workspace keeps its business data and team access separate."}
        </p>
        {creating ? (
          <form className="create-org-form" onSubmit={submit}>
            <label>
              Organization name
              <input
                name="name"
                required
                placeholder="Your business name"
                autoFocus
              />
            </label>
            <label>
              Business email <em>Optional</em>
              <input
                type="email"
                name="email"
                placeholder="hello@company.com"
              />
            </label>
            <div>
              <button
                type="button"
                className="app-btn secondary"
                onClick={() => setCreating(false)}
              >
                Cancel
              </button>
              <button
                className="app-btn primary"
                disabled={createState.isLoading}
              >
                {createState.isLoading ? "Creating…" : "Create workspace"}
              </button>
            </div>
          </form>
        ) : (
          <>
            <div className="org-list">
              {isLoading && <p>Loading workspaces…</p>}
              {error && (
                <div className="org-load-error">
                  <strong>Unable to load workspaces</strong>
                  <span>Please sign in again to continue.</span>
                  <Link className="app-btn secondary" to="/login">
                    Go to login
                  </Link>
                </div>
              )}
              {organizations.map((organization) => (
                <Link
                  key={organization.id}
                  to={`/app/${organization.id}/dashboard`}
                >
                  <i>{organization.name.slice(0, 2).toUpperCase()}</i>
                  <span>
                    <b>{organization.name}</b>
                    <small>{organization.role}</small>
                  </span>
                  <em>Open workspace →</em>
                </Link>
              ))}
              {!isLoading && !error && !organizations.length && (
                <p>No organizations found.</p>
              )}
            </div>
            <button
              className="app-btn secondary"
              onClick={() => setCreating(true)}
            >
              + Create organization
            </button>
          </>
        )}
      </section>
    </main>
  );
}

import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
  useParams,
} from "react-router";
import { useDispatch, useSelector } from "react-redux";
import { WorkspaceShell } from "./AppWorkspaceShell";
import { Icon } from "../../../app/application/Ui";
import { organizationSelected } from "../../../app/store/slices";
import {
  useCreateOrganizationMutation,
  useMeQuery,
  useOrganizationsQuery,
  usePublicAnnouncementsQuery,
  usePublicPlatformSettingsQuery,
} from "../../../app/store/api";

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
  const { data: platformSettings } = usePublicPlatformSettingsQuery();
  const { data: announcementsData } = usePublicAnnouncementsQuery({
    activeOnly: true,
  });
  const activeAnnouncements = Array.isArray(announcementsData?.items)
    ? announcementsData.items.filter((item) => item.is_active)
    : [];
  const maintenanceMessage =
    platformSettings?.maintenance_message ||
    "Scheduled maintenance is in progress. Please check back shortly.";
  const maintenanceBanner =
    platformSettings?.maintenance_notice_enabled ||
    activeAnnouncements.length > 0
      ? {
          title: platformSettings?.maintenance_notice_enabled
            ? "Scheduled maintenance"
            : activeAnnouncements[0]?.title,
          message: platformSettings?.maintenance_notice_enabled
            ? maintenanceMessage
            : activeAnnouncements[0]?.message || maintenanceMessage,
        }
      : null;
  const organization = organizations.find(
    (item) => String(item.id) === String(organizationId),
  );
  const organizationName = organization?.name || "Organization";
  const organizationRole = organization?.role
    ? roleLabel(organization.role)
    : "Member";
  const userName = user?.full_name || "there";
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
    <WorkspaceShell
      collapsed={collapsed}
      setCollapsed={setCollapsed}
      mobile={mobile}
      setMobile={setMobile}
      orgOpen={orgOpen}
      setOrgOpen={setOrgOpen}
      organizationName={organizationName}
      organizationRole={organizationRole}
      userName={userName}
      userEmail={user?.email || ""}
      online={online}
      syncMessage={syncMessage}
      maintenanceBanner={maintenanceBanner}
      base={base}
      segment={segment}
      names={names}
      mainNavContent={navItems(mainNav)}
      manageNavContent={navItems(manageNav)}
      orgOptions={orgOptions}
      navigate={navigate}
      organizationId={organizationId}
    >
      <Outlet context={{ online }} />
    </WorkspaceShell>
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

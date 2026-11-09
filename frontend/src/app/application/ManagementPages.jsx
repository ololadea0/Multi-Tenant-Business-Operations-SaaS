import { useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router";
import { useOfflineQueue, useOrganizationData } from "../store/dataHooks";
import { Icon, Notice, PageHeader, Search, Status } from "./Ui";
import {
  useCreateInvitationMutation,
  useInvitationsQuery,
  useLeaveOrganizationMutation,
  useOrganizationQuery,
  useRemoveMemberMutation,
  useResendInvitationMutation,
  useRevokeInvitationMutation,
  useUpdateMemberRoleMutation,
  useUpdateOrganizationMutation,
} from "../store/api";
import { useMeQuery, useUpdateMeMutation } from "../store/api";

const normalizeRole = (role) => String(role ?? "").toUpperCase();

export function Activity() {
  const { activities } = useOrganizationData();
  const [search, setSearch] = useState("");
  const rows = activities.filter((a) =>
    (a.action + a.user + a.detail).toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <>
      <PageHeader
        eyebrow="WORKSPACE HISTORY"
        title="Activity"
        description="A clear record of important actions across this organization."
      />
      <div className="activity-controls">
        <Search
          value={search}
          onChange={setSearch}
          placeholder="Search activity"
        />
        <select>
          <option>All categories</option>
          <option>Orders</option>
          <option>Inventory</option>
          <option>Products</option>
          <option>Team</option>
        </select>
        <select>
          <option>Last 30 days</option>
          <option>Last 7 days</option>
          <option>Today</option>
        </select>
      </div>
      <section className="activity-history">
        <div className="history-day">
          <span>Today</span>
          <i />
        </div>
        {rows.slice(0, 3).map((a, i) => (
          <div className="history-row" key={a.action}>
            <i className={`history-icon h${i}`}>
              <Icon
                name={
                  a.category === "Order" ? "orders" : a.category.toLowerCase()
                }
              />
            </i>
            <div>
              <b>{a.action}</b>
              <p>{a.detail}</p>
            </div>
            <Status>{a.category}</Status>
            <span>{a.user}</span>
            <time>{a.time}</time>
          </div>
        ))}
        <div className="history-day">
          <span>Yesterday</span>
          <i />
        </div>
        {rows.slice(3).map((a, i) => (
          <div className="history-row" key={a.action}>
            <i className={`history-icon h${i + 3}`}>
              <Icon name={a.category.toLowerCase()} />
            </i>
            <div>
              <b>{a.action}</b>
              <p>{a.detail}</p>
            </div>
            <Status>{a.category}</Status>
            <span>{a.user}</span>
            <time>{a.time}</time>
          </div>
        ))}
      </section>
    </>
  );
}

export function Team() {
  const { organizationId } = useParams();
  const { team } = useOrganizationData();
  const { data: organization } = useOrganizationQuery(organizationId, {
    skip: !organizationId,
  });
  const canManageRoles = ["OWNER", "ADMIN"].includes(
    normalizeRole(organization?.role),
  );
  const [selectedMember, setSelectedMember] = useState(null);
  const [roleOpen, setRoleOpen] = useState(false);
  const [removeOpen, setRemoveOpen] = useState(false);
  const [menuMemberId, setMenuMemberId] = useState(null);
  const [updateMemberRole, updateRoleState] = useUpdateMemberRoleMutation();
  const [removeMember, removeState] = useRemoveMemberMutation();
  return (
    <>
      <PageHeader
        eyebrow="PEOPLE & ACCESS"
        title="Team"
        description="Manage active members and make each person’s access clear."
        action={
          <Link
            className="app-btn primary"
            to={`/app/${organizationId}/invitations`}
          >
            Invite a member
          </Link>
        }
      />
      <div className="role-explainer">
        <div>
          <span>OWNER</span>
          <p>Full control of the organization, members and settings.</p>
        </div>
        <div>
          <span>ADMIN</span>
          <p>Manages operations, team access and most settings.</p>
        </div>
        <div>
          <span>MANAGER</span>
          <p>Manages daily operations and business records.</p>
        </div>
        <div>
          <span>STAFF</span>
          <p>Works with permitted day-to-day records.</p>
        </div>
      </div>
      <div className="record-surface">
        <div className="panel-heading padded">
          <div>
            <span>Active members</span>
            <small>{team.length} people in this workspace</small>
          </div>
        </div>
        <div className="app-table-wrap">
          <table className="app-table">
            <thead>
              <tr>
                <th>Member</th>
                <th>Role</th>
                <th>Status</th>
                <th>Last active</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {team.map((m) => (
                <tr key={m.email}>
                  <td>
                    <div className="primary-cell">
                      <i>{m.initials}</i>
                      <span>
                        <b>
                          {m.name}
                          {m.isMe && <small className="you-label">You</small>}
                        </b>
                        <small>{m.email}</small>
                      </span>
                    </div>
                  </td>
                  <td>
                    <button
                      className="role-button"
                      disabled={!canManageRoles || m.isMe}
                      onClick={() =>
                        !m.isMe &&
                        canManageRoles &&
                        (setSelectedMember(m), setRoleOpen(true))
                      }
                    >
                      {normalizeRole(m.role)}
                      <Icon name="chevron" />
                    </button>
                  </td>
                  <td>
                    <Status>{m.status}</Status>
                  </td>
                  <td>{m.last}</td>
                  <td>
                    <div className="menu-wrap">
                      <button
                        type="button"
                        className="row-menu"
                        disabled={!canManageRoles || m.isMe}
                        onClick={() =>
                          setMenuMemberId((current) =>
                            current === m.user_id ? null : m.user_id,
                          )
                        }
                      >
                        •••
                      </button>
                      {menuMemberId === m.user_id && (
                        <div className="invite-menu">
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedMember(m);
                              setRoleOpen(true);
                              setMenuMemberId(null);
                            }}
                          >
                            Change role
                          </button>
                          <button
                            type="button"
                            className="danger"
                            onClick={() => {
                              setSelectedMember(m);
                              setRemoveOpen(true);
                              setMenuMemberId(null);
                            }}
                            disabled={removeState.isLoading}
                          >
                            Remove member
                          </button>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {roleOpen && selectedMember && (
        <RoleDialog
          member={selectedMember}
          close={() => {
            setRoleOpen(false);
            setSelectedMember(null);
          }}
        />
      )}
      {removeOpen && selectedMember && (
        <RemoveMemberDialog
          member={selectedMember}
          close={() => {
            setRemoveOpen(false);
            setSelectedMember(null);
          }}
        />
      )}
    </>
  );
}

function RoleDialog({ member, close }) {
  const { organizationId } = useParams();
  const [role, setRole] = useState(normalizeRole(member?.role || "MANAGER"));
  const [updateMemberRole, updateRoleState] = useUpdateMemberRoleMutation();

  async function confirmRoleChange() {
    if (!member?.user_id) return;
    await updateMemberRole({
      organizationId,
      userId: member.user_id,
      role: role.toLowerCase(),
    });
    close();
  }

  return (
    <div className="dialog-layer">
      <button type="button" className="dialog-scrim" onClick={close} />
      <div className="app-dialog role-dialog">
        <header>
          <div>
            <span>TEAM ACCESS</span>
            <h2>Change {member?.name || "member"}'s role</h2>
          </div>
          <button type="button" onClick={close}>
            ×
          </button>
        </header>
        <p>
          Choose the level of access this team member should have in this
          organization.
        </p>
        {[
          ["ADMIN", "Manage operations, team access and settings."],
          ["MANAGER", "Manage daily operations and business records."],
          ["STAFF", "Work with permitted day-to-day records."],
        ].map((r) => (
          <button
            type="button"
            className={`role-option ${role === r[0] ? "active" : ""}`}
            onClick={() => setRole(r[0])}
            key={r[0]}
          >
            <i />
            <span>
              <b>{r[0]}</b>
              <small>{r[1]}</small>
            </span>
          </button>
        ))}
        <footer>
          <button type="button" className="app-btn secondary" onClick={close}>
            Cancel
          </button>
          <button
            type="button"
            className="app-btn primary"
            onClick={confirmRoleChange}
            disabled={
              updateRoleState.isLoading || role === normalizeRole(member?.role)
            }
          >
            {updateRoleState.isLoading ? "Updating…" : "Update role"}
          </button>
        </footer>
      </div>
    </div>
  );
}

function RemoveMemberDialog({ member, close }) {
  const { organizationId } = useParams();
  const [removeMember, removeState] = useRemoveMemberMutation();

  async function confirmRemove() {
    if (!member?.user_id) return;
    await removeMember({ organizationId, userId: member.user_id }).unwrap();
    close();
  }

  return (
    <div className="dialog-layer">
      <button type="button" className="dialog-scrim" onClick={close} />
      <div className="confirm-dialog">
        <div className="warning-icon">
          <Icon name="alert" />
        </div>
        <h2>Remove this member?</h2>
        <p>
          This will revoke {member?.name || "this member"}'s access to the
          workspace immediately. They will lose their current permissions and no
          longer be able to view or edit organization records.
        </p>
        <div>
          <button type="button" className="app-btn secondary" onClick={close}>
            Keep member
          </button>
          <button
            type="button"
            className="app-btn danger-fill"
            onClick={confirmRemove}
            disabled={removeState.isLoading}
          >
            {removeState.isLoading ? "Removing…" : "Remove member"}
          </button>
        </div>
      </div>
    </div>
  );
}

export function Invitations() {
  const { organizationId } = useParams();
  const { data: invitations = [] } = useInvitationsQuery(organizationId, {
    skip: !organizationId,
  });
  const [createInvitation, invitationState] = useCreateInvitationMutation();
  const [resendInvitation] = useResendInvitationMutation();
  const [revokeInvitation] = useRevokeInvitationMutation();
  const [openInvitation, setOpenInvitation] = useState(null);
  async function submit(e) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      await createInvitation({
        organizationId,
        email: form.get("email"),
        role: String(form.get("role") || "staff")
          .split(" ")[0]
          .toLowerCase(),
      }).unwrap();
      e.currentTarget.reset();
    } catch {}
  }
  return (
    <>
      <PageHeader
        eyebrow="PEOPLE & ACCESS"
        title="Invitations"
        description="Invite people to this workspace and follow pending access."
      />
      <div className="invite-layout">
        <form className="invite-form" onSubmit={submit}>
          <div>
            <h2>Invite a team member</h2>
            <p>
              They’ll receive an email with a secure link to join this
              organization.
            </p>
          </div>
          {invitationState.isSuccess && (
            <Notice tone="success">
              Invitation email sent successfully. The recipient can use the
              secure link in their inbox.
            </Notice>
          )}
          {invitationState.error && (
            <Notice tone="error">
              {invitationState.error?.data?.detail ||
                "The invitation email could not be sent. Please try again."}
            </Notice>
          )}
          <label>
            Email address
            <input
              required
              name="email"
              type="email"
              placeholder="colleague@company.com"
            />
          </label>
          <label>
            Organization role
            <select name="role" defaultValue="staff">
              <option>STAFF — Day-to-day access</option>
              <option>MANAGER — Operations management</option>
              <option>ADMIN — Administrative access</option>
            </select>
          </label>
          <button
            className="app-btn primary"
            disabled={invitationState.isLoading}
          >
            {invitationState.isLoading ? "Sending…" : "Send invitation"}
          </button>
        </form>
        <section className="pending-invites">
          <div className="panel-heading">
            <div>
              <span>Pending invitations</span>
              <small>
                {invitations.length}{" "}
                {invitations.length === 1 ? "person has" : "people have"} not
                joined yet
              </small>
            </div>
          </div>
          {invitations.map((invitation) => (
            <div className="invite-row" key={invitation.id}>
              <div className="mail-mark">@</div>
              <span>
                <b>{invitation.email}</b>
                <small>
                  {invitation.role} ·{" "}
                  {new Date(invitation.created_at).toLocaleDateString()}
                </small>
              </span>
              <Status>Pending</Status>
              <div className="invite-actions">
                <button
                  type="button"
                  aria-label="Invitation actions"
                  onClick={() =>
                    setOpenInvitation(
                      openInvitation === invitation.id ? null : invitation.id,
                    )
                  }
                >
                  •••
                </button>
                {openInvitation === invitation.id && (
                  <div className="invite-menu">
                    <button
                      type="button"
                      onClick={async () => {
                        await resendInvitation({
                          organizationId,
                          invitationId: invitation.id,
                        }).unwrap();
                        setOpenInvitation(null);
                      }}
                    >
                      Resend invitation
                    </button>
                    <button
                      type="button"
                      className="danger"
                      onClick={async () => {
                        await revokeInvitation({
                          organizationId,
                          invitationId: invitation.id,
                        }).unwrap();
                        setOpenInvitation(null);
                      }}
                    >
                      Revoke invitation
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </section>
      </div>
    </>
  );
}

export function Settings() {
  const { organizationId } = useParams();
  const { data: organization, isLoading } = useOrganizationQuery(
    organizationId,
    {
      skip: !organizationId,
    },
  );
  const [updateOrganization, updateState] = useUpdateOrganizationMutation();
  const [leaveOrganization, leaveState] = useLeaveOrganizationMutation();
  const isOwner = String(organization?.role ?? "").toUpperCase() === "OWNER";
  const [form, setForm] = useState({
    name: "",
    email: "",
    address_line_1: "",
    city: "",
    state: "",
    postal_code: "",
    country: "",
    phone: "",
    website: "",
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (organization) {
      setForm({
        name: organization.name || "",
        email: organization.email || "",
        address_line_1: organization.address_line_1 || "",
        city: organization.city || "",
        state: organization.state || "",
        postal_code: organization.postal_code || "",
        country: organization.country || "",
        phone: organization.phone || "",
        website: organization.website || "",
      });
    }
  }, [organization]);

  function handleChange(event) {
    const { name, value } = event.target;
    const sanitizedValue =
      name === "phone" ? value.replace(/\D/g, "").slice(0, 11) : value;
    setForm((current) => ({ ...current, [name]: sanitizedValue }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!isOwner) return;
    await updateOrganization({ organizationId, ...form });
    setSaved(true);
  }

  async function handleLeaveOrganization() {
    if (isOwner) return;
    const confirmed = window.confirm(
      "Leave this organization? You will lose access immediately.",
    );
    if (!confirmed) return;
    await leaveOrganization(organizationId).unwrap();
    window.location.assign("/app");
  }

  return (
    <>
      <PageHeader
        eyebrow="ORGANIZATION"
        title="Settings"
        description="Manage the information and preferences for this organization."
      />
      <div className="settings-layout">
        <nav>
          <a className="active" href="#general">
            General
          </a>
          <a href="#operations">Operations</a>
          <a href="#danger">Organization management</a>
        </nav>
        <form onSubmit={handleSubmit}>
          <section id="general" className="settings-section">
            <header>
              <h2>Organization information</h2>
              <p>Shown to members across this workspace.</p>
            </header>
            {saved && (
              <Notice>
                {updateState.isLoading
                  ? "Saving changes…"
                  : "Organization settings saved."}
              </Notice>
            )}
            {!isOwner && (
              <Notice tone="warning">
                Only the organization owner can edit these settings.
              </Notice>
            )}
            <label>
              Organization name
              <input
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="Your organization name"
                disabled={isLoading || updateState.isLoading || !isOwner}
              />
            </label>
            <label>
              Business email
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="contact@yourcompany.com"
                disabled={isLoading || updateState.isLoading || !isOwner}
              />
            </label>
            <label>
              Address
              <input
                name="address_line_1"
                value={form.address_line_1}
                onChange={handleChange}
                placeholder="Street address"
                disabled={!isOwner}
              />
            </label>
            <div className="field-row">
              <label>
                City
                <input
                  name="city"
                  value={form.city}
                  onChange={handleChange}
                  placeholder="City"
                  disabled={!isOwner}
                />
              </label>
              <label>
                State
                <input
                  name="state"
                  value={form.state}
                  onChange={handleChange}
                  placeholder="State or region"
                  disabled={!isOwner}
                />
              </label>
            </div>
            <div className="field-row">
              <label>
                Postal code
                <input
                  name="postal_code"
                  value={form.postal_code}
                  onChange={handleChange}
                  placeholder="Postal code"
                  disabled={!isOwner}
                />
              </label>
              <label>
                Country
                <input
                  name="country"
                  value={form.country}
                  onChange={handleChange}
                  placeholder="Country"
                  disabled={!isOwner}
                />
              </label>
            </div>
            <div className="field-row">
              <label>
                Phone number
                <input
                  type="tel"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={11}
                  name="phone"
                  value={form.phone}
                  onChange={handleChange}
                  placeholder="08000000000"
                  disabled={!isOwner}
                />
              </label>
              <label>
                Website
                <input
                  name="website"
                  value={form.website}
                  onChange={handleChange}
                  placeholder="https://yourcompany.com"
                  disabled={!isOwner}
                />
              </label>
            </div>
            <button
              className="app-btn primary"
              disabled={updateState.isLoading || !isOwner}
            >
              {updateState.isLoading ? "Saving…" : "Save changes"}
            </button>
          </section>
          <section id="operations" className="settings-section">
            <header>
              <h2>Operations</h2>
              <p>Default values used in records and summaries.</p>
            </header>
            <div className="field-row">
              <label>
                Currency
                <select defaultValue="NGN">
                  <option>NGN — Nigerian Naira</option>
                  <option>GBP — British Pound</option>
                </select>
              </label>
              <label>
                Time zone
                <select>
                  <option>Pacific Time (UTC−08:00)</option>
                </select>
              </label>
            </div>
          </section>
          <section id="danger" className="settings-section danger-zone">
            <header>
              <h2>Organization management</h2>
              <p>High-impact actions require owner access.</p>
            </header>
            <div>
              <span>
                <b>Leave this organization</b>
                <small>
                  Transfer ownership before leaving if you are the only owner.
                </small>
              </span>
              <button
                type="button"
                className="app-btn secondary"
                disabled={isOwner || leaveState.isLoading}
                onClick={handleLeaveOrganization}
              >
                {leaveState.isLoading
                  ? "Leaving…"
                  : isOwner
                    ? "Owner cannot leave"
                    : "Leave organization"}
              </button>
            </div>
          </section>
        </form>
      </div>
    </>
  );
}

export function Profile() {
  const { data: user, isLoading } = useMeQuery();
  const [updateMe, updateState] = useUpdateMeMutation();
  async function saveProfile(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    await updateMe({
      full_name: `${data.get("first_name")} ${data.get("last_name")}`.trim(),
    });
  }
  return (
    <>
      <PageHeader
        eyebrow="PERSONAL ACCOUNT"
        title="Your profile"
        description="Manage your personal information and account access."
      />
      <div className="profile-layout">
        <section className="profile-card">
          <div className="large-avatar">
            {(user?.full_name || "")
              .split(" ")
              .map((part) => part[0])
              .join("")
              .slice(0, 2)
              .toUpperCase()}
          </div>
          <div>
            <h2>
              {user?.full_name ||
                (isLoading ? "Loading profile…" : "Your profile")}
            </h2>
            <p>{user?.email || "Account details"}</p>
            <Status>Account active</Status>
          </div>
          <button className="app-btn secondary">Change photo</button>
        </section>
        <form className="profile-form" onSubmit={saveProfile}>
          <div>
            <h2>Personal information</h2>
            <p>This information is shown to people in your workspaces.</p>
          </div>
          <div className="field-row">
            <label>
              First name
              <input
                name="first_name"
                defaultValue={user?.full_name?.split(" ")[0] || ""}
                placeholder="Your first name"
                required
              />
            </label>
            <label>
              Last name
              <input
                name="last_name"
                defaultValue={
                  user?.full_name?.split(" ").slice(1).join(" ") || ""
                }
                placeholder="Your last name"
              />
            </label>
          </div>
          <label>
            Email address
            <input value={user?.email || ""} disabled readOnly />
            <small>Email is managed by your sign-in provider.</small>
          </label>
          <button className="app-btn primary" disabled={updateState.isLoading}>
            {updateState.isLoading ? "Saving…" : "Save profile"}
          </button>
          {updateState.isSuccess && (
            <Notice tone="success">Profile updated successfully.</Notice>
          )}
          {updateState.error && (
            <Notice tone="error">
              {updateState.error?.data?.detail ||
                "Profile could not be updated."}
            </Notice>
          )}
        </form>
        <section className="profile-form">
          <div>
            <h2>Sign-in and security</h2>
            <p>Your sign-in credentials are managed securely by Daymark.</p>
          </div>
          <button className="app-btn secondary">Review active sessions</button>
          <Link className="app-btn danger-outline" to="/login">
            Log out
          </Link>
        </section>
      </div>
    </>
  );
}

export function SyncCentre() {
  const { online } = useOutletContext();
  const { organizationId } = useOrganizationData();
  const queue = useOfflineQueue(organizationId);
  const [retrying, setRetrying] = useState(false);
  const [conflict, setConflict] = useState(false);
  return (
    <>
      <PageHeader
        eyebrow="OFFLINE & SYNC"
        title="Sync centre"
        description="See what is saved on this device, what has reached Daymark, and what needs you."
        action={
          <div className={`sync-state-large ${online ? "online" : ""}`}>
            <i />
            <span>
              <b>{online ? "Connected" : "Offline"}</b>
              <small>
                {online ? "Last synced a moment ago" : "Using saved data"}
              </small>
            </span>
          </div>
        }
      />
      <Notice tone="warning">
        The supported operation list and conflict contract require API
        verification before production wiring.
      </Notice>
      <section className="sync-overview">
        <div>
          <span>Pending actions</span>
          <strong>
            {
              queue.filter((item) =>
                ["pending", "failed"].includes(item.status),
              ).length
            }
          </strong>
          <small>Saved safely on this device</small>
        </div>
        <div>
          <span>Failed actions</span>
          <strong>
            {queue.filter((item) => item.status === "failed").length}
          </strong>
          <small>Needs another attempt</small>
        </div>
        <div>
          <span>Conflicts</span>
          <strong>
            {queue.filter((item) => item.status === "conflict").length}
          </strong>
          <small>Requires a decision</small>
        </div>
        <div>
          <span>Last successful sync</span>
          <strong className="sync-time">09:42</strong>
          <small>Today · 2 minutes ago</small>
        </div>
      </section>
      <div className="sync-layout">
        <section className="sync-queue">
          <div className="panel-heading">
            <div>
              <span>Action queue</span>
              <small>Changes waiting to reach the server</small>
            </div>
            <button
              className="app-btn secondary"
              onClick={() => setRetrying(true)}
            >
              {retrying ? "Synchronizing…" : "Sync now"}
            </button>
          </div>
          {queue.map((item, i) => (
            <div className="queue-row" key={item.operationId}>
              <i className={item.status === "failed" ? "failed" : ""}>
                {item.status === "failed" ? "!" : i + 1}
              </i>
              <span>
                <b>{item.type}</b>
                <small>
                  {item.resource} · {new Date(item.createdAt).toLocaleString()}
                </small>
              </span>
              <Status>{retrying ? "Synchronizing" : item.status}</Status>
              {item.status === "failed" && <button>Retry</button>}
            </div>
          ))}
        </section>
        <aside className="sync-health">
          <span>CONNECTION DETAIL</span>
          <dl>
            <div>
              <dt>Network</dt>
              <dd>{online ? "Online" : "Offline"}</dd>
            </div>
            <div>
              <dt>Cached data</dt>
              <dd>Updated 2 min ago</dd>
            </div>
            <div>
              <dt>Local storage</dt>
              <dd>Available</dd>
            </div>
          </dl>
          <p>
            Some information may be stale while offline. Each screen shows the
            last known synchronization time where relevant.
          </p>
        </aside>
      </div>
      <section className="conflict-panel">
        <div>
          <span>CONFLICT REQUIRING ATTENTION</span>
          <h2>Queued change conflict</h2>
          <p>
            A queued change differs from the current server version. Choose
            which version to keep.
          </p>
        </div>
        <div className="version-compare">
          <article>
            <span>SAVED ON THIS DEVICE · 09:31</span>
            <p>The locally saved version is waiting for your decision.</p>
            <button onClick={() => setConflict(true)}>Keep this version</button>
          </article>
          <article>
            <span>IN DAYMARK · 09:38</span>
            <p>The server version is available for comparison.</p>
            <button onClick={() => setConflict(true)}>
              Keep server version
            </button>
          </article>
        </div>
        {conflict && (
          <Notice>
            Choice recorded locally. Server confirmation is required before
            marking this conflict resolved.
          </Notice>
        )}
      </section>
    </>
  );
}

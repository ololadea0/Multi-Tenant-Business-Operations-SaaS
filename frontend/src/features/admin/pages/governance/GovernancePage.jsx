import {
  useAnnouncementsQuery,
  useCreateAnnouncementMutation,
  useAuditLogsQuery,
} from "../../../../app/store/api";
import { Status } from "../../../../app/application/Ui";
import { AdminHead } from "../../components/AdminShell";

export function Announcements() {
  const { data, isLoading } = useAnnouncementsQuery({ activeOnly: false });
  const [createAnnouncement, { isLoading: creating }] =
    useCreateAnnouncementMutation();
  const announcements = data?.items ?? [];

  async function handleSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const startsAt = formData.get("starts_at");
    const endsAt = formData.get("ends_at");
    const payload = {
      title: String(formData.get("title") || "").trim(),
      message: String(formData.get("message") || "").trim(),
      kind: String(formData.get("kind") || "announcement"),
      is_active: String(formData.get("is_active") || "on") === "on",
      starts_at: startsAt ? new Date(String(startsAt)).toISOString() : null,
      ends_at: endsAt ? new Date(String(endsAt)).toISOString() : null,
    };

    if (!payload.title || !payload.message) return;
    await createAnnouncement(payload).unwrap();
    event.currentTarget.reset();
  }

  return (
    <>
      <AdminHead
        label="COMMUNICATION"
        title="Announcements"
        copy="Publish policy updates and product updates to customer workspaces."
      />

      {isLoading && (
        <p style={{ margin: "0 0 18px", color: "#59655f" }}>
          Loading announcements...
        </p>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.1fr 0.9fr",
          gap: "20px",
        }}
      >
        <form
          onSubmit={handleSubmit}
          style={{
            background: "#fff",
            borderRadius: "20px",
            padding: "20px",
            border: "1px solid rgba(17,25,23,0.04)",
            boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
            display: "grid",
            gap: "12px",
          }}
        >
          <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
            Title
            <input
              name="title"
              placeholder="Scheduled maintenance"
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                padding: "11px 12px",
              }}
            />
          </label>
          <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
            Message
            <textarea
              name="message"
              rows={5}
              placeholder="We are applying a patch to the platform..."
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                padding: "11px 12px",
                resize: "vertical",
              }}
            />
          </label>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
              gap: "12px",
            }}
          >
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Type
              <select
                name="kind"
                defaultValue="announcement"
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              >
                <option value="announcement">Announcement</option>
                <option value="maintenance">Maintenance</option>
                <option value="notice">Notice</option>
              </select>
            </label>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Active
              <select
                name="is_active"
                defaultValue="on"
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              >
                <option value="on">Yes</option>
                <option value="off">No</option>
              </select>
            </label>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
              gap: "12px",
            }}
          >
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Starts at
              <input
                type="datetime-local"
                name="starts_at"
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              />
            </label>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Ends at
              <input
                type="datetime-local"
                name="ends_at"
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              />
            </label>
          </div>
          <button
            type="submit"
            disabled={creating}
            style={{
              border: 0,
              background: "#111917",
              color: "#fff",
              borderRadius: "12px",
              padding: "12px 16px",
              fontWeight: 700,
            }}
          >
            {creating ? "Publishing..." : "Publish announcement"}
          </button>
        </form>

        <div style={{ display: "grid", gap: "14px" }}>
          {announcements.length === 0 && (
            <div
              style={{
                background: "#fff",
                borderRadius: "20px",
                padding: "20px",
                border: "1px solid rgba(17,25,23,0.04)",
              }}
            >
              <p style={{ margin: 0, color: "#586863" }}>
                No announcements yet.
              </p>
            </div>
          )}
          {announcements.map((announcement) => (
            <div
              key={announcement.id}
              style={{
                background: "#fff",
                borderRadius: "20px",
                padding: "20px",
                border: "1px solid rgba(17,25,23,0.04)",
                boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: "12px",
                  marginBottom: "10px",
                }}
              >
                <b style={{ fontSize: "1.1rem" }}>{announcement.title}</b>
                <Status>{announcement.kind}</Status>
              </div>
              <p style={{ margin: "0 0 10px", color: "#586863" }}>
                {announcement.message}
              </p>
              <small style={{ color: "#5d675f" }}>
                {announcement.is_active ? "Active" : "Inactive"} •{" "}
                {announcement.starts_at
                  ? new Date(announcement.starts_at).toLocaleString()
                  : "Immediate"}
              </small>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

export function FeatureFlags() {
  return (
    <>
      <AdminHead
        label="CONTROL CENTRE"
        title="Feature Flags"
        copy="Enable or disable product capabilities across environments and tenant cohorts."
      />
      <div
        style={{
          background: "#fff",
          borderRadius: "20px",
          padding: "20px",
          border: "1px solid rgba(17,25,23,0.04)",
        }}
      >
        <p style={{ margin: 0, color: "#586863" }}>
          Feature flag configuration will be connected to the platform settings
          layer in the next release.
        </p>
      </div>
    </>
  );
}

export function SecurityAccess() {
  return (
    <>
      <AdminHead
        label="ACCESS MANAGEMENT"
        title="Security & Access"
        copy="Review platform role policies, authentication posture and administrative controls."
      />
      <div
        style={{
          background: "#fff",
          borderRadius: "20px",
          padding: "20px",
          border: "1px solid rgba(17,25,23,0.04)",
        }}
      >
        <p style={{ margin: 0, color: "#586863" }}>
          Platform security controls are enforced server-side and are ready for
          role expansion.
        </p>
      </div>
    </>
  );
}

export function Backups() {
  return (
    <>
      <AdminHead
        label="INFRASTRUCTURE"
        title="Backup Monitoring"
        copy="Monitor backup integrity, retention and restore readiness for the Daymark platform."
      />
      <div
        style={{
          background: "#fff",
          borderRadius: "20px",
          padding: "20px",
          border: "1px solid rgba(17,25,23,0.04)",
        }}
      >
        <p style={{ margin: 0, color: "#586863" }}>
          Backup and restore monitoring is available as the platform operations
          layer matures.
        </p>
      </div>
    </>
  );
}

export function AuditLogs() {
  const { data, isLoading, error } = useAuditLogsQuery({ page: 1, limit: 20 });

  const logs = (data?.items ?? []).map((entry) => {
    const timestamp = entry.created_at
      ? new Date(entry.created_at).toLocaleString("en-GB", {
          day: "2-digit",
          month: "short",
          hour: "2-digit",
          minute: "2-digit",
        })
      : "—";

    return [
      entry.actor_name || "System",
      entry.description || entry.action || "Platform event",
      entry.entity_type || "platform",
      timestamp,
      entry.source || "platform-admin",
    ];
  });

  const rows = logs;

  return (
    <>
      <AdminHead
        label="ADMINISTRATION HISTORY"
        title="Audit Logs"
        copy="Track administrative actions and important automated platform events."
      />

      {isLoading && (
        <p style={{ margin: "0 0 20px", color: "#59655f" }}>
          Loading platform audit trail...
        </p>
      )}

      {error && (
        <div
          style={{
            background: "#fff3f1",
            color: "#7a2d24",
            borderRadius: "12px",
            padding: "12px 14px",
            marginBottom: "18px",
            border: "1px solid rgba(122,45,36,0.08)",
          }}
        >
          Unable to load audit logs right now.
        </div>
      )}

      <div
        style={{
          background: "#fff",
          borderRadius: "22px",
          border: "1px solid rgba(17,25,23,0.04)",
          boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
          padding: "18px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "12px",
            marginBottom: "12px",
            flexWrap: "wrap",
          }}
        >
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <select
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                background: "#fff",
                padding: "10px 12px",
              }}
            >
              <option>All actors</option>
              <option>Administrators</option>
              <option>System</option>
            </select>
            <select
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                background: "#fff",
                padding: "10px 12px",
              }}
            >
              <option>Last 30 days</option>
              <option>Last 7 days</option>
            </select>
          </div>
          <button
            style={{
              border: 0,
              borderRadius: "12px",
              background: "#111917",
              color: "#fff",
              padding: "10px 14px",
              fontWeight: 700,
            }}
          >
            Export CSV
          </button>
        </div>

        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {["Actor", "Action", "Entity", "Timestamp", "Source"].map(
                (column) => (
                  <th
                    key={column}
                    style={{
                      textAlign: "left",
                      padding: "10px 8px",
                      color: "#586863",
                      fontSize: "12px",
                      letterSpacing: "0.08em",
                      textTransform: "uppercase",
                    }}
                  >
                    {column}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {rows.map(([actor, action, entity, timestamp, source], index) => (
              <tr
                key={`${actor}-${index}`}
                style={{ borderTop: "1px solid rgba(17,25,23,0.06)" }}
              >
                <td style={{ padding: "12px 8px", fontWeight: 700 }}>
                  {actor}
                </td>
                <td style={{ padding: "12px 8px" }}>{action}</td>
                <td style={{ padding: "12px 8px", color: "#5d675f" }}>
                  {entity}
                </td>
                <td style={{ padding: "12px 8px", color: "#5d675f" }}>
                  {timestamp}
                </td>
                <td style={{ padding: "12px 8px" }}>
                  <Status>{source}</Status>
                </td>
              </tr>
            ))}
            {!isLoading && !error && rows.length === 0 && (
              <tr>
                <td colSpan="5" style={{ padding: "24px 8px", color: "#5d675f" }}>
                  No platform audit events have been recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

import { Status } from "../../../../app/application/Ui";
import { EmailCentreShell } from "../../components/AdminShell";
import { useEmailHistoryQuery } from "../../../../app/store/api";

export function EmailHistory() {
  const { data, isLoading } = useEmailHistoryQuery();
  const rows = data?.items || [];

  return (
    <EmailCentreShell
      title="Email History"
      subtitle="Review every admin email, its lifecycle status, and retry/backoff history."
      tabs={[
        ["Overview", "/admin/email-centre"],
        ["Compose", "/admin/email-centre/compose"],
        ["Templates", "/admin/email-centre/templates"],
        ["Automation", "/admin/email-centre/automation"],
        ["History", "/admin/email-centre/history"],
      ]}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: "22px",
          padding: "18px",
          border: "1px solid rgba(17,25,23,0.04)",
          boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              {["Campaign", "Recipient", "Status", "Timestamp"].map(
                (column) => (
                  <th
                    key={column}
                    style={{
                      textAlign: "left",
                      color: "#586863",
                      fontSize: "12px",
                      letterSpacing: "0.08em",
                      textTransform: "uppercase",
                      padding: "10px 8px",
                    }}
                  >
                    {column}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {rows.map((email) => (
              <tr
                key={email.id}
                style={{ borderTop: "1px solid rgba(17,25,23,0.06)" }}
              >
                <td style={{ padding: "12px 8px", fontWeight: 700 }}>
                  {email.subject}
                </td>
                <td style={{ padding: "12px 8px" }}>{email.recipient_email}</td>
                <td style={{ padding: "12px 8px" }}>
                  <Status>{email.status}</Status>
                </td>
                <td style={{ padding: "12px 8px", color: "#5d675f" }}>
                  {email.created_at ? new Date(email.created_at).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
            {!isLoading && rows.length === 0 && (
              <tr>
                <td colSpan="4" style={{ padding: "24px 8px", color: "#5d675f" }}>
                  No email delivery records yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </EmailCentreShell>
  );
}

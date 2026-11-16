import { Status } from "../../../../app/application/Ui";
import { EmailCentreShell } from "../../components/AdminShell";

export function EmailAutomation() {
  const automation = [
    ["Welcome sequence", "Enabled", "Triggered after sign-up"],
    ["Trial reminder", "Enabled", "7 days before expiry"],
    ["Renewal notice", "Enabled", "3 days before renewal"],
    ["Marketing digest", "Preference-based", "Weekly to opted-in users"],
  ];

  return (
    <EmailCentreShell
      title="Automated Emails"
      subtitle="Lifecycle and policy-based emails sent without manual effort."
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
              {["Workflow", "Status", "Trigger"].map((column) => (
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
              ))}
            </tr>
          </thead>
          <tbody>
            {automation.map(([workflow, status, trigger]) => (
              <tr
                key={workflow}
                style={{ borderTop: "1px solid rgba(17,25,23,0.06)" }}
              >
                <td style={{ padding: "12px 8px", fontWeight: 700 }}>
                  {workflow}
                </td>
                <td style={{ padding: "12px 8px" }}>
                  <Status>{status}</Status>
                </td>
                <td style={{ padding: "12px 8px", color: "#5d675f" }}>
                  {trigger}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </EmailCentreShell>
  );
}

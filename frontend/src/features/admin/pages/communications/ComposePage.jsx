import { useState } from "react";
import {
  useEmailPreviewMutation,
  useEmailSendMutation,
} from "../../../../app/store/api";
import { EmailCentreShell, PanelHead } from "../../components/AdminShell";

export function EmailCompose() {
  const [preview, setPreview] = useState(null);
  const [send, { isLoading: sending }] = useEmailSendMutation();
  const [previewMutation, { isLoading: previewing }] =
    useEmailPreviewMutation();

  const handlePreview = async (event) => {
    event.preventDefault();
    const formNode = event.currentTarget.form ?? event.currentTarget;
    const form = new FormData(formNode);
    const payload = {
      template_key: String(form.get("template_key") || "announcement"),
      recipient_email: String(
        form.get("recipient_email") || "customer@example.com",
      ),
      subject: String(form.get("subject") || ""),
      variables: {
        first_name: String(form.get("first_name") || "Ada"),
        announcement_message: String(
          form.get("message") || "Your platform update is ready.",
        ),
      },
      is_promotional: String(form.get("is_promotional") === "on"),
    };
    const result = await previewMutation(payload).unwrap();
    setPreview(result);
  };

  const handleSend = async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = {
      template_key: String(form.get("template_key") || "announcement"),
      recipient_email: String(
        form.get("recipient_email") || "customer@example.com",
      ),
      subject: String(form.get("subject") || "Daymark update"),
      variables: {
        first_name: String(form.get("first_name") || "Ada"),
        announcement_message: String(
          form.get("message") || "Your platform update is ready.",
        ),
      },
      is_promotional: String(form.get("is_promotional") === "on"),
      idempotency_key: `admin-email-${Date.now()}`,
      test_only: String(form.get("test_only") === "on"),
    };
    await send(payload).unwrap();
    alert("Email queued successfully.");
  };

  return (
    <EmailCentreShell
      title="Compose Email"
      subtitle="Preview templates, run a test send, and send policy-safe messages to customers or teams."
      tabs={[
        ["Overview", "/admin/email-centre"],
        ["Compose", "/admin/email-centre/compose"],
        ["Templates", "/admin/email-centre/templates"],
        ["Automation", "/admin/email-centre/automation"],
        ["History", "/admin/email-centre/history"],
      ]}
    >
      <div
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}
      >
        <form
          onSubmit={handleSend}
          style={{
            background: "#fff",
            borderRadius: "22px",
            padding: "22px",
            border: "1px solid rgba(17,25,23,0.04)",
            boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
          }}
        >
          <PanelHead
            title="Campaign composer"
            copy="Branded HTML templates with Jinja2 rendering"
          />
          <div style={{ display: "grid", gap: "12px" }}>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Template
              <select
                name="template_key"
                defaultValue="announcement"
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              >
                <option value="announcement">Announcement</option>
                <option value="welcome">Welcome</option>
                <option value="billing">Billing</option>
              </select>
            </label>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Recipient email
              <input
                name="recipient_email"
                defaultValue="customer@example.com"
                type="email"
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              />
            </label>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Subject
              <input
                name="subject"
                defaultValue="Quarterly update"
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              />
            </label>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              First name
              <input
                name="first_name"
                defaultValue="Ada"
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
                defaultValue="We’ve shipped a new set of operational improvements for your team."
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
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "12px",
                border: "1px solid rgba(17,25,23,0.08)",
                borderRadius: "14px",
                padding: "12px 14px",
              }}
            >
              <div>
                <b>Promotional email</b>
                <br />
                <small style={{ color: "#5d675f" }}>
                  Optional announcement or marketing content
                </small>
              </div>
              <input type="checkbox" name="is_promotional" />
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "12px",
                border: "1px solid rgba(17,25,23,0.08)",
                borderRadius: "14px",
                padding: "12px 14px",
              }}
            >
              <div>
                <b>Test email only</b>
                <br />
                <small style={{ color: "#5d675f" }}>No bulk send</small>
              </div>
              <input type="checkbox" name="test_only" defaultChecked />
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: "10px",
                marginTop: "8px",
              }}
            >
              <button
                type="button"
                onClick={handlePreview}
                disabled={previewing}
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  background: "#fff",
                  borderRadius: "12px",
                  padding: "11px 16px",
                  fontWeight: 700,
                }}
              >
                {previewing ? "Generating preview..." : "Preview email"}
              </button>
              <button
                type="submit"
                disabled={sending}
                style={{
                  border: 0,
                  background: "#111917",
                  color: "#fff",
                  borderRadius: "12px",
                  padding: "11px 16px",
                  fontWeight: 700,
                }}
              >
                {sending ? "Sending..." : "Send email"}
              </button>
            </div>
          </div>
        </form>

        <div
          style={{
            background: "#fff",
            borderRadius: "22px",
            padding: "22px",
            border: "1px solid rgba(17,25,23,0.04)",
            boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
          }}
        >
          <PanelHead
            title="Preview"
            copy="Rendered HTML as it will appear to recipients"
          />
          {preview ? (
            <div dangerouslySetInnerHTML={{ __html: preview.html }} />
          ) : (
            <p style={{ margin: 0, color: "#5d675f" }}>
              Preview will appear here before your message is sent.
            </p>
          )}
        </div>
      </div>
    </EmailCentreShell>
  );
}

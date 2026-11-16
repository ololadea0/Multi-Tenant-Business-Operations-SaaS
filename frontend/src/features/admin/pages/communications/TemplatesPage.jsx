import { Status } from "../../../../app/application/Ui";
import { EmailCentreShell } from "../../components/AdminShell";
import { EmailTemplatePreview, emailTemplateOptions } from "../../../../emails/EmailTemplates";
import { useState } from "react";

export function EmailTemplates() {
  const [selected, setSelected] = useState("verification");
  const [viewport, setViewport] = useState("desktop");
  const templates = [
    ["Welcome", "Transaction", "welcome"],
    ["Platform announcement", "Marketing", "announcement"],
    ["Billing summary", "Transaction", "billing"],
  ];

  return (
    <EmailCentreShell
      title="Email Templates"
      subtitle="Reusable branded templates for essential and optional messaging."
      tabs={[
        ["Overview", "/admin/email-centre"],
        ["Compose", "/admin/email-centre/compose"],
        ["Templates", "/admin/email-centre/templates"],
        ["Automation", "/admin/email-centre/automation"],
        ["History", "/admin/email-centre/history"],
      ]}
    >
      <div style={{ display: "grid", gridTemplateColumns: "220px minmax(0, 1fr)", gap: "18px", alignItems: "start" }}>
        <div style={{ display: "grid", gap: "6px" }}>
          {emailTemplateOptions.map((item) => <button key={item.key} type="button" onClick={() => setSelected(item.key)} style={{ textAlign: "left", border: "1px solid rgba(17,25,23,.1)", background: selected === item.key ? "#17211e" : "#fff", color: selected === item.key ? "#fff" : "#17211e", padding: "12px 14px", fontWeight: 700, cursor: "pointer" }}>{item.label}</button>)}
        </div>
        <div style={{ minWidth: 0, border: "1px solid rgba(17,25,23,.08)", background: "#eef1ed", overflow: "auto", padding: 16 }}>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 6, marginBottom: 12 }}>
            {[['desktop', 'Desktop'], ['mobile', 'Mobile']].map(([key, label]) => (
              <button key={key} type="button" onClick={() => setViewport(key)} style={{ border: "1px solid rgba(17,25,23,.12)", background: viewport === key ? "#17211e" : "#fff", color: viewport === key ? "#fff" : "#17211e", padding: "7px 10px", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>{label}</button>
            ))}
          </div>
          <div style={{ maxWidth: viewport === "mobile" ? 390 : 760, margin: "0 auto", transition: "max-width .2s ease" }}><EmailTemplatePreview template={selected} /></div>
        </div>
      </div>
      <div style={{ display: "none" }}>
        {templates.map(([name, type, key]) => (
          <div
            key={key}
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
              }}
            >
              <div>
                <b style={{ display: "block", fontSize: "1.1rem" }}>{name}</b>
                <small style={{ color: "#5d675f" }}>{type} email</small>
              </div>
              <Status>{type === "Marketing" ? "Optional" : "Essential"}</Status>
            </div>
            <p style={{ color: "#586863", margin: "16px 0 0" }}>
              Jinja2-rendered template with Daymark branding and a compliant
              opt-in treatment for promotional sends.
            </p>
          </div>
        ))}
      </div>
    </EmailCentreShell>
  );
}

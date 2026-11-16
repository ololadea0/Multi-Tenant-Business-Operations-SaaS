import { EmailCentreShell, PanelHead } from "../../components/AdminShell";
import { useEmailMetricsQuery } from "../../../../app/store/api";

export function EmailCentreOverview() {
  const { data: metrics, isLoading } = useEmailMetricsQuery();
  const cards = [
    ["Delivered this month", metrics?.delivered_this_month ?? "—", "Sent records"],
    ["Open rate", metrics?.open_rate == null ? "Not tracked" : `${metrics.open_rate}%`, "Provider tracking required"],
    ["Transactional sends", metrics?.transactional_this_month ?? "—", "Current month"],
    ["Promo sends", metrics?.promotional_this_month ?? "—", "Current month"],
  ];
  const volume = metrics?.monthly_volume || [];
  const maxVolume = Math.max(...volume.map((item) => item.count), 1);

  return (
    <EmailCentreShell
      title="Email Centre"
      subtitle="Monitor campaigns, automate lifecycle messaging, and protect customer trust with policy-aware sends."
      tabs={[
        ["Overview", "/admin/email-centre"],
        ["Compose", "/admin/email-centre/compose"],
        ["Templates", "/admin/email-centre/templates"],
        ["Automation", "/admin/email-centre/automation"],
        ["History", "/admin/email-centre/history"],
      ]}
    >
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "18px",
          marginBottom: "22px",
        }}
      >
        {cards.map(([label, value, trend]) => (
          <div
            key={label}
            style={{
              background: "#fff",
              borderRadius: "20px",
              padding: "20px",
              border: "1px solid rgba(17,25,23,0.04)",
              boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
            }}
          >
            <span
              style={{
                display: "block",
                color: "#5d675f",
                fontSize: "12px",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}
            >
              {label}
            </span>
            <b
              style={{
                display: "block",
                fontSize: "2.2rem",
                marginTop: "10px",
              }}
            >
              {value}
            </b>
            <small style={{ color: "#0d6c3d" }}>{trend}</small>
          </div>
        ))}
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "1.3fr 0.7fr",
          gap: "20px",
        }}
      >
        <div
          style={{
            background: "#fff",
            borderRadius: "22px",
            padding: "22px",
            border: "1px solid rgba(17,25,23,0.04)",
            boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
          }}
        >
          <PanelHead title="Email volume" copy={isLoading ? "Loading delivery records…" : "Messages created over the last 12 months"} />
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(12, minmax(0, 1fr))",
              gap: "10px",
              alignItems: "end",
              height: "220px",
              paddingTop: "18px",
            }}
          >
            {volume.map((item, index) => (
                <div
                  key={index}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "flex-end",
                    height: "100%",
                  }}
                >
                  <i
                    style={{
                      width: "100%",
                      maxWidth: "28px",
                      height: `${Math.max((item.count / maxVolume) * 160, item.count ? 8 : 2)}px`,
                      display: "block",
                      background:
                        "linear-gradient(180deg, #ffb7a7 0%, #ff5c35 100%)",
                      borderRadius: "8px 8px 0 0",
                    }}
                  />
                  <span
                    style={{
                      marginTop: "10px",
                      fontSize: "11px",
                      color: "#5d675f",
                    }}
                  >
                    {item.month}
                  </span>
                </div>
              ),
            )}
          </div>
        </div>

        <div
          style={{
            background: "#fff",
            borderRadius: "22px",
            padding: "22px",
            border: "1px solid rgba(17,25,23,0.04)",
            boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
          }}
        >
          <PanelHead title="Email policy" copy="Platform safeguards" />
          <ul
            style={{
              listStyle: "none",
              padding: 0,
              margin: 0,
              display: "grid",
              gap: "12px",
            }}
          >
            {[
              ["Idempotent sends", "Same campaign key cannot be sent twice"],
              [
                "Retry backoff",
                "Temporary failures retry with exponential delay",
              ],
              ["Audit trail", "Every admin send is recorded"],
              [
                "Preference-aware marketing",
                "Optional announcements respect opt-ins",
              ],
            ].map(([label, copy]) => (
              <li
                key={label}
                style={{
                  padding: "10px 0",
                  borderTop: "1px solid rgba(17,25,23,0.06)",
                }}
              >
                <b style={{ display: "block" }}>{label}</b>
                <small style={{ color: "#5d675f" }}>{copy}</small>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </EmailCentreShell>
  );
}

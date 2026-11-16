import { Link } from "react-router";

const metrics = [
  { label: "Businesses", value: "0", detail: "Active workspaces" },
  { label: "Users", value: "0", detail: "Across all teams" },
  { label: "Subscriptions", value: "0", detail: "Plans in motion" },
  { label: "Revenue", value: "$0", detail: "This month" },
];

const sections = [
  "Businesses",
  "Users",
  "Subscriptions",
  "Payments",
  "Plans & Pricing",
  "Analytics",
  "Platform Settings",
  "Audit Logs",
];

export function AdminDashboard() {
  return (
    <main
      className="admin-shell"
      style={{
        minHeight: "100vh",
        background: "#f3f4f0",
        padding: "32px 24px 80px",
      }}
    >
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "16px",
            marginBottom: "32px",
          }}
        >
          <div>
            <p
              style={{
                margin: 0,
                color: "#5c665d",
                textTransform: "uppercase",
                letterSpacing: "0.12em",
                fontSize: "12px",
                fontWeight: 700,
              }}
            >
              Platform administration
            </p>
            <h1
              style={{
                margin: "8px 0 0",
                fontSize: "clamp(2rem, 4vw, 3rem)",
                color: "#111a17",
              }}
            >
              Daymark control centre
            </h1>
          </div>

          <Link
            to="/login"
            style={{
              textDecoration: "none",
              background: "#111a17",
              color: "#f7f5f1",
              borderRadius: "999px",
              padding: "12px 18px",
              fontWeight: 700,
            }}
          >
            Switch account
          </Link>
        </div>

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "18px",
            marginBottom: "28px",
          }}
        >
          {metrics.map((metric) => (
            <article
              key={metric.label}
              style={{
                background: "#fff",
                borderRadius: "18px",
                padding: "22px 20px",
                boxShadow: "0 8px 22px rgba(18, 25, 23, 0.06)",
              }}
            >
              <p
                style={{
                  margin: 0,
                  color: "#5c665d",
                  fontSize: "13px",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                }}
              >
                {metric.label}
              </p>
              <h2
                style={{
                  margin: "14px 0 6px",
                  fontSize: "2rem",
                  color: "#111a17",
                }}
              >
                {metric.value}
              </h2>
              <small style={{ color: "#5c665d" }}>{metric.detail}</small>
            </article>
          ))}
        </section>

        <section
          style={{
            background: "#fff",
            borderRadius: "24px",
            padding: "24px",
            boxShadow: "0 12px 30px rgba(18, 25, 23, 0.06)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "18px",
            }}
          >
            <h3 style={{ margin: 0, color: "#111a17", fontSize: "1.3rem" }}>
              Platform overview
            </h3>
            <span
              style={{
                color: "#0d7a4d",
                background: "#dff5e7",
                padding: "8px 12px",
                borderRadius: "999px",
                fontWeight: 700,
              }}
            >
              Live
            </span>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "14px",
            }}
          >
            {sections.map((label) => (
              <div
                key={label}
                style={{
                  border: "1px solid #e4e7e1",
                  borderRadius: "14px",
                  padding: "18px 16px",
                  background: "#fbfcfa",
                  color: "#1b241f",
                  fontWeight: 600,
                }}
              >
                {label}
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

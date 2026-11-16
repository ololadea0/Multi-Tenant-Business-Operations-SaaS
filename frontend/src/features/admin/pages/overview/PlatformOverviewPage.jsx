import { useAdminDashboardQuery } from "../../../../app/store/api";
import { AdminHead } from "../../components/AdminShell";
import { Status } from "../../../../app/application/Ui";

const emptyResponse = {
  totals: { users: 0, organizations: 0, subscriptions: 0, payments: 0 },
  businesses: [],
  users: [],
  subscriptions: [],
  payments: [],
};

export function AdminOverview() {
  const { data, isLoading } = useAdminDashboardQuery();
  const totals = data?.totals ?? emptyResponse.totals;
  const recentBusinesses = (data?.businesses ?? []).slice(0, 4);

  return (
    <>
      <AdminHead
        label="PLATFORM OVERVIEW"
        title="The whole platform, in view."
        copy="Monitor customers, subscriptions and revenue across Daymark."
        action={
          <select
            style={{
              minWidth: "150px",
              borderRadius: "12px",
              border: "1px solid rgba(17,25,23,0.14)",
              background: "#fff",
              padding: "11px 12px",
            }}
          >
            <option>Last 30 days</option>
            <option>This quarter</option>
          </select>
        }
      />

      {isLoading && (
        <p style={{ margin: "0 0 20px", color: "#59655f" }}>
          Loading platform metrics...
        </p>
      )}

      <section
        style={{
          display: "grid",
          gap: "18px",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          marginBottom: "28px",
        }}
      >
        {[
          [
            "Total businesses",
            totals.organizations ?? 0,
            "Across all workspaces",
          ],
          [
            "Active subscriptions",
            totals.subscriptions ?? 0,
            "Platform subscription records",
          ],
          ["Total users", totals.users ?? 0, "Across every business"],
          ["Platform payments", totals.payments ?? 0, "Recorded transactions"],
        ].map(([label, value, note]) => (
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
                color: "#5d675f",
                fontSize: "12px",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              {label}
            </span>
            <strong
              style={{
                display: "block",
                fontSize: "2.25rem",
                marginTop: "8px",
              }}
            >
              {value}
            </strong>
            <small style={{ color: "#55615c" }}>{note}</small>
          </div>
        ))}
      </section>

      <section
        style={{
          display: "grid",
          gap: "20px",
          gridTemplateColumns: "2fr 1fr",
          marginBottom: "28px",
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
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "10px",
              marginBottom: "20px",
            }}
          >
            <div>
              <b style={{ display: "block", fontSize: "1.1rem" }}>
                Revenue growth
              </b>
              <small style={{ color: "#5d675f" }}>
                Monthly recurring revenue · 6 months
              </small>
            </div>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "52px 1fr",
              gap: "14px",
            }}
          >
            <div
              style={{
                color: "#5d675f",
                fontSize: "12px",
                display: "grid",
                alignContent: "space-between",
              }}
            >
              <span>₦3m</span>
              <span>₦2m</span>
              <span>₦1m</span>
              <span>₦0</span>
            </div>
            <div>
              <svg
                viewBox="0 0 600 190"
                style={{ width: "100%", height: "190px" }}
                preserveAspectRatio="none"
              >
                <path
                  d="M0 160C80 150 80 125 145 130s80-45 145-35 70-30 135-23 90-35 175-55v180H0Z"
                  fill="rgba(255,92,53,0.14)"
                />
                <path
                  d="M0 160C80 150 80 125 145 130s80-45 145-35 70-30 135-23 90-35 175-55"
                  fill="none"
                  stroke="#ff5c35"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              </svg>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(6, 1fr)",
                  color: "#5d675f",
                  fontSize: "11px",
                  marginTop: "6px",
                }}
              >
                {["JAN", "FEB", "MAR", "APR", "MAY", "JUN"].map((item) => (
                  <span key={item}>{item}</span>
                ))}
              </div>
            </div>
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
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: "10px",
              marginBottom: "16px",
            }}
          >
            <div>
              <b style={{ display: "block", fontSize: "1.1rem" }}>
                Subscription mix
              </b>
              <small style={{ color: "#5d675f" }}>
                Active businesses by plan
              </small>
            </div>
          </div>
          <div
            style={{ display: "grid", placeItems: "center", margin: "18px 0" }}
          >
            <div
              style={{
                width: "190px",
                height: "190px",
                borderRadius: "50%",
                background:
                  "conic-gradient(#111917 0 39%, #ff5c35 39% 85%, #dfe5df 85% 100%)",
                position: "relative",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  inset: "24px",
                  background: "#fff",
                  borderRadius: "50%",
                  display: "grid",
                  placeItems: "center",
                  textAlign: "center",
                }}
              >
                <div>
                  <b style={{ fontSize: "1.8rem" }}>186</b>
                  <small style={{ display: "block", color: "#5d675f" }}>
                    active
                  </small>
                </div>
              </div>
            </div>
          </div>
          <ul
            style={{
              listStyle: "none",
              padding: 0,
              margin: 0,
              display: "grid",
              gap: "10px",
            }}
          >
            {[
              ["Starter", "72", "39%", "#dfe5df"],
              ["Growth", "86", "46%", "#111917"],
              ["Scale", "28", "15%", "#ff5c35"],
            ].map(([label, value, percent, colour]) => (
              <li
                key={label}
                style={{
                  display: "grid",
                  gridTemplateColumns: "14px 1fr auto auto",
                  gap: "10px",
                  alignItems: "center",
                  color: "#1d241f",
                  fontWeight: 600,
                }}
              >
                <i
                  style={{
                    width: "10px",
                    height: "10px",
                    borderRadius: "50%",
                    background: colour,
                    display: "inline-block",
                  }}
                />
                <span>{label}</span>
                <b>{value}</b>
                <span style={{ color: "#5d675f" }}>{percent}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gap: "20px",
          gridTemplateColumns: "1.2fr 0.8fr",
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
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: "12px",
              marginBottom: "16px",
            }}
          >
            <div>
              <b style={{ display: "block", fontSize: "1.1rem" }}>
                Recent businesses
              </b>
              <small style={{ color: "#5d675f" }}>
                Newest organizations on Daymark
              </small>
            </div>
            <button
              style={{
                border: "0",
                background: "transparent",
                color: "#111917",
                fontWeight: 700,
              }}
            >
              View businesses →
            </button>
          </div>
          {recentBusinesses.map((business, index) => (
            <div
              key={business.id ?? business.name}
              style={{
                display: "grid",
                gridTemplateColumns: "42px 1fr auto auto",
                alignItems: "center",
                gap: "12px",
                padding: "12px 0",
                borderTop: index === 0 ? "0" : "1px solid rgba(17,25,23,0.06)",
              }}
            >
              <i
                style={{
                  width: "38px",
                  height: "38px",
                  borderRadius: "50%",
                  background: "#eff1ee",
                  display: "grid",
                  placeItems: "center",
                  fontWeight: 700,
                }}
              >
                {business.name
                  .split(" ")
                  .map((part) => part[0])
                  .join("")
                  .slice(0, 2)}
              </i>
              <div>
                <b style={{ display: "block" }}>{business.name}</b>
                <small style={{ color: "#5d675f" }}>
                  {business.owner_email}
                </small>
              </div>
              <Status>{business.status ?? "Active"}</Status>
              <time style={{ color: "#5d675f" }}>{business.created_at}</time>
            </div>
          ))}
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
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: "12px",
              marginBottom: "16px",
            }}
          >
            <div>
              <b style={{ display: "block", fontSize: "1.1rem" }}>
                Needs attention
              </b>
              <small style={{ color: "#5d675f" }}>
                Platform items requiring review
              </small>
            </div>
          </div>
          {[
            ["7 failed renewals", "Payment retry window is active", "!"],
            ["14 trials ending soon", "Within the next 7 days", "!"],
            ["3 suspended businesses", "Administrator action required", "i"],
          ].map(([title, copy, icon]) => (
            <div
              key={title}
              style={{
                display: "grid",
                gridTemplateColumns: "34px 1fr auto",
                alignItems: "center",
                gap: "10px",
                padding: "10px 0",
              }}
            >
              <span
                style={{
                  width: "28px",
                  height: "28px",
                  borderRadius: "50%",
                  background: "#f7f8f6",
                  display: "grid",
                  placeItems: "center",
                  fontWeight: 700,
                }}
              >
                {icon}
              </span>
              <div>
                <b style={{ display: "block" }}>{title}</b>
                <small style={{ color: "#5d675f" }}>{copy}</small>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

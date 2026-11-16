import { useAnalyticsQuery } from "../../../../app/store/api";
import { AdminHead } from "../../components/AdminShell";

export function Analytics() {
  const { data, isLoading } = useAnalyticsQuery();
  const summary = data?.summary ?? {};

  const stats = [
    [
      "Net revenue",
      `₦${Number(summary.mrr || 0).toLocaleString("en-NG")}`,
      "Live MRR",
    ],
    ["Businesses", String(summary.organizations ?? 0), "Total organizations"],
    ["Users", String(summary.users ?? 0), "Platform users"],
    ["Payments", String(summary.payments ?? 0), "Recorded transactions"],
  ];

  return (
    <>
      <AdminHead
        label="PLATFORM INTELLIGENCE"
        title="Analytics"
        copy="Understand revenue, growth, churn and subscription movement."
      />

      {isLoading && (
        <p style={{ margin: "0 0 20px", color: "#59655f" }}>
          Loading platform analytics...
        </p>
      )}

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
          gap: "18px",
          marginBottom: "24px",
        }}
      >
        {stats.map(([label, value, change]) => (
          <div
            key={label}
            style={{
              background: "#fff",
              borderRadius: "18px",
              padding: "18px 16px",
              border: "1px solid rgba(17,25,23,0.04)",
              boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
            }}
          >
            <span
              style={{
                display: "block",
                color: "#5d675f",
                fontSize: "12px",
                textTransform: "uppercase",
                letterSpacing: "0.08em",
              }}
            >
              {label}
            </span>
            <b
              style={{
                display: "block",
                fontSize: "2rem",
                margin: "12px 0 8px",
              }}
            >
              {value}
            </b>
            <small style={{ color: "#0d6c3d" }}>{change}</small>
          </div>
        ))}
      </section>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.4fr 0.6fr",
          gap: "20px",
        }}
      >
        <section
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
              alignItems: "center",
              gap: "12px",
              marginBottom: "18px",
            }}
          >
            <div>
              <b style={{ display: "block" }}>Live subscription snapshot</b>
              <small style={{ color: "#5d675f" }}>
                Current platform health
              </small>
            </div>
          </div>
          <div style={{ display: "grid", gap: "12px" }}>
            {[
              ["Active subscriptions", summary.active_subscriptions ?? 0],
              ["Trials", summary.trial_subscriptions ?? 0],
              ["Past due", summary.past_due_subscriptions ?? 0],
              ["Suspended businesses", summary.suspended_businesses ?? 0],
            ].map(([label, value]) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  paddingTop: "8px",
                  borderTop: "1px solid rgba(17,25,23,0.06)",
                }}
              >
                <span style={{ color: "#5d675f" }}>{label}</span>
                <b>{value}</b>
              </div>
            ))}
          </div>
        </section>

        <section
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
              alignItems: "center",
              gap: "12px",
              marginBottom: "18px",
            }}
          >
            <div>
              <b style={{ display: "block" }}>Payment movement</b>
              <small style={{ color: "#5d675f" }}>
                Live transaction health
              </small>
            </div>
          </div>
          {[
            [
              "Successful payments",
              summary.successful_payments ?? 0,
              "positive",
            ],
            ["Failed payments", summary.failed_payments ?? 0, "negative"],
            [
              "ARR",
              `₦${Number(summary.arr || 0).toLocaleString("en-NG")}`,
              "positive",
            ],
          ].map(([label, value, tone]) => (
            <div
              key={label}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "12px",
                padding: "10px 0",
                borderTop: "1px solid rgba(17,25,23,0.06)",
              }}
            >
              <span>{label}</span>
              <b
                style={{
                  color:
                    tone === "positive"
                      ? "#0d6c3d"
                      : tone === "negative"
                        ? "#c9392f"
                        : "#565d58",
                }}
              >
                {value}
              </b>
            </div>
          ))}
        </section>
      </div>
    </>
  );
}

import { usePlatformHealthQuery } from "../../../../app/store/api";
import { AdminHead } from "../../components/AdminShell";

export function SystemHealth() {
  const { data, isLoading } = usePlatformHealthQuery();
  const records = data?.records ?? {};
  const warnings = data?.warnings ?? [];

  const healthCards = [
    [
      "API status",
      data?.status === "ok" ? "Operational" : "Degraded",
      data?.status === "ok" ? "Healthy" : "Alert",
      data?.status === "ok" ? "#0d6c3d" : "#7a2d24",
    ],
    [
      "Database",
      data?.database_connected ? "Connected" : "Disconnected",
      data?.database_connected ? "Healthy" : "Critical",
      data?.database_connected ? "#0d6c3d" : "#7a2d24",
    ],
    [
      "Billing worker",
      data?.billing_worker_running ? "Running" : "Stopped",
      data?.billing_worker_running ? "Healthy" : "Warning",
      data?.billing_worker_running ? "#0d6c3d" : "#b45d10",
    ],
    [
      "Email service",
      data?.email_service_ready ? "Configured" : "Missing key",
      data?.email_service_ready ? "Healthy" : "Warning",
      data?.email_service_ready ? "#0d6c3d" : "#b45d10",
    ],
    [
      "Payment gateway",
      data?.payment_service_ready ? "Configured" : "Missing key",
      data?.payment_service_ready ? "Healthy" : "Warning",
      data?.payment_service_ready ? "#0d6c3d" : "#b45d10",
    ],
    [
      "Last billing cycle",
      data?.billing_worker_last_cycle_at
        ? new Date(data.billing_worker_last_cycle_at).toLocaleString()
        : "Never",
      data?.billing_worker_last_cycle_at ? "Synced" : "Idle",
      data?.billing_worker_last_cycle_at ? "#0d6c3d" : "#7a2d24",
    ],
    ["Organizations", String(records.organizations ?? 0), "Tracked", "#3c4b46"],
    ["Users", String(records.users ?? 0), "Registered", "#3c4b46"],
    [
      "Subscriptions",
      String(records.subscriptions ?? 0),
      "Active records",
      "#3c4b46",
    ],
    ["Payments", String(records.payments ?? 0), "Transactions", "#3c4b46"],
  ];

  return (
    <>
      <AdminHead
        label="PLATFORM OPERATIONS"
        title="System Health"
        copy="Monitor uptime, service readiness and platform health across Daymark services."
      />

      {isLoading && (
        <p style={{ margin: "0 0 20px", color: "#59655f" }}>
          Loading live system health...
        </p>
      )}

      <div
        style={{
          display: "grid",
          gap: "18px",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          marginBottom: "24px",
        }}
      >
        {healthCards.map(([label, value, status, color]) => (
          <div
            key={label}
            style={{
              background: "#fff",
              borderRadius: "20px",
              padding: "20px",
              border: "1px solid rgba(17,25,23,0.04)",
            }}
          >
            <span
              style={{
                color: "#5d675f",
                fontSize: "12px",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}
            >
              {label}
            </span>
            <strong
              style={{ display: "block", marginTop: "12px", fontSize: "2rem" }}
            >
              {value}
            </strong>
            <small
              style={{
                color,
                fontWeight: 700,
              }}
            >
              {status}
            </small>
          </div>
        ))}
      </div>

      <div
        style={{
          background: "#fff",
          borderRadius: "20px",
          padding: "20px",
          border: "1px solid rgba(17,25,23,0.04)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "12px",
            marginBottom: "14px",
          }}
        >
          <span
            style={{
              color: "#5d675f",
              fontSize: "12px",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
            }}
          >
            Warnings
          </span>
          <span
            style={{
              background: warnings.length ? "#fff3e5" : "#ebf9f0",
              color: warnings.length ? "#b45d10" : "#0d6c3d",
              borderRadius: "999px",
              padding: "6px 10px",
              fontSize: "12px",
              fontWeight: 700,
            }}
          >
            {warnings.length ? `${warnings.length} active` : "No warnings"}
          </span>
        </div>

        {warnings.length ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {warnings.map((warning) => (
              <span
                key={warning}
                style={{
                  display: "inline-flex",
                  background: "#fff3e5",
                  color: "#8c4d10",
                  borderRadius: "999px",
                  padding: "7px 12px",
                  fontSize: "12px",
                  fontWeight: 600,
                }}
              >
                {warning}
              </span>
            ))}
          </div>
        ) : (
          <p style={{ margin: 0, color: "#586863" }}>
            No operational warnings reported.
          </p>
        )}
      </div>
    </>
  );
}

export function SupportTickets() {
  return (
    <>
      <AdminHead
        label="CUSTOMER CARE"
        title="Support Tickets"
        copy="Track open customer issues, escalations and team response timelines."
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
          No live ticket feed is connected yet, but the support workspace is now
          mounted and ready for the service layer.
        </p>
      </div>
    </>
  );
}

export function FeedbackBoard() {
  return (
    <>
      <AdminHead
        label="PRODUCT FEEDBACK"
        title="Feedback & Feature Requests"
        copy="Capture requests from accounts, sales teams and customer success workstreams."
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
          Feature requests will be surfaced here once the platform feedback
          collection is connected.
        </p>
      </div>
    </>
  );
}

export function Promotions() {
  return (
    <>
      <AdminHead
        label="COMMERCIAL TOOLS"
        title="Promotions & Coupons"
        copy="Manage discounts, trials and campaign codes used across the Daymark platform."
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
          Promotion configuration is ready for the next marketing rules rollout.
        </p>
      </div>
    </>
  );
}

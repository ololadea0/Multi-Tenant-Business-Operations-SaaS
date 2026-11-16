import { EmailButton, EmailLayout, EmailText } from "./components/EmailLayout";

const sample = {
  verification: {
    eyebrow: "WELCOME TO DAYMARK",
    title: "Verify your email",
    body: (
      <>
        Hi Ada,
        <br />
        <br />
        Confirm your email address to activate your Daymark workspace and start
        managing products, inventory and customer orders from one clear view.
      </>
    ),
    summary: {
      title: "Workspace snapshot",
      rows: [
        ["Business", "Northstar Studio"],
        ["Owner", "Ada Thompson"],
        ["Status", "Verification ready"],
      ],
    },
    action: "Verify email address",
    note: "This link expires in 30 minutes. If you did not create this account, you can safely ignore this email.",
  },
  reset: {
    eyebrow: "ACCOUNT SECURITY",
    title: "Reset your password",
    body: (
      <>
        We received a request to change your Daymark password. Use the button
        below to choose a new one and keep your workspace secure.
      </>
    ),
    summary: {
      title: "Security check",
      rows: [
        ["Requested", "Today at 09:14"],
        ["Session", "Web app"],
        ["Risk", "Low"],
      ],
    },
    action: "Reset password",
    note: "This link expires in 30 minutes. If you did not request this action, your account will remain unchanged.",
  },
  invitation: {
    eyebrow: "TEAM INVITATION",
    title: "You’re invited to join Joy Williamson's Organization",
    body: (
      <>
        <strong>Joy Williamson</strong> invited you to join{" "}
        <strong>Joy Williamson&apos;s Organization</strong> on Daymark as a{" "}
        <strong>Staff</strong>.
      </>
    ),
    summary: {
      title: "Invitation details",
      rows: [
        ["Invited by", "Joy Williamson"],
        ["Role", "Staff access"],
        ["Expires", "20 Nov 2026 • 05:28 UTC"],
      ],
    },
    action: "Accept invitation",
    note: "You received this email because someone invited you to join an organization on Daymark. If you were not expecting this invitation, you can safely ignore this email.",
  },
  welcome: {
    eyebrow: "YOUR DAYMARK WORKSPACE",
    title: "Welcome to Daymark, Ada",
    body: (
      <>
        Your workspace is ready. Start by adding your first product, inviting
        your team, or recording your next order.
      </>
    ),
    summary: {
      title: "Start here",
      rows: [
        ["Products", "Add your catalog"],
        ["Team", "Invite collaborators"],
        ["Orders", "Track each sale"],
      ],
    },
    action: "Go to Daymark",
    note: "You are receiving this message because a Daymark account was created for you.",
  },
  announcement: {
    eyebrow: "DAYMARK UPDATE",
    title: "A clearer way to run your business",
    body: (
      <>
        We have improved the tools that help you keep products, customers and
        orders moving together, with clearer visibility and calmer workflows.
      </>
    ),
    summary: {
      title: "What’s new",
      rows: [
        ["Inventory", "Cleaner stock views"],
        ["Orders", "Faster fulfilment"],
        ["Insights", "Clearer reporting"],
      ],
    },
    action: "See what’s new",
    note: "You are receiving this message because you subscribed to optional Daymark updates.",
  },
  receipt: {
    eyebrow: "NORTHSTAR STUDIO • RECEIPT",
    title: "Receipt #DM-1048",
    body: (
      <>
        <strong>Thank you, Ada.</strong>
        <br />
        <br />
        Your order has been recorded and the details below are ready for your
        records.
      </>
    ),
    summary: {
      title: "Order summary",
      rows: [
        ["2 × Ceramic mug", "₦18,000"],
        ["Service fee", "₦0"],
        ["Total paid", "₦18,000"],
      ],
    },
    action: "View receipt",
    note: "This email was sent on behalf of Northstar Studio regarding a transaction recorded in its system.",
  },
  billing: {
    eyebrow: "MONTHLY BILLING",
    title: "Your billing summary is ready",
    body: (
      <>
        Your Daymark subscription is active and your latest billing summary is
        attached below for review.
      </>
    ),
    summary: {
      title: "Billing snapshot",
      rows: [
        ["Plan", "Growth"],
        ["Next invoice", "24 Nov 2026"],
        ["Amount due", "₦84,500"],
      ],
    },
    action: "Open billing",
    note: "This invoice reflects your current subscription and the active workspace settings at the time of billing.",
  },
};

export function EmailTemplatePreview({ template = "verification" }) {
  const item = sample[template] || sample.verification;

  return (
    <EmailLayout
      eyebrow={item.eyebrow}
      title={item.title}
      action={<EmailButton>{item.action}</EmailButton>}
      disclaimer={item.note}
    >
      <EmailText>{item.body}</EmailText>

      {item.summary && (
        <div
          style={{
            marginTop: 18,
            marginBottom: 12,
            background: "#f5f2ed",
            border: "1px solid #e4ddd2",
            borderRadius: 18,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "12px 16px",
              borderBottom: "1px solid #e8dfd5",
              background: "rgba(255,255,255,0.4)",
              fontSize: 11,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              color: "#677772",
              fontWeight: 700,
            }}
          >
            {item.summary.title}
          </div>
          <div style={{ padding: "14px 16px 10px" }}>
            {item.summary.rows.map(([label, value]) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 10,
                  padding: "8px 0",
                  borderBottom:
                    label === item.summary.rows[item.summary.rows.length - 1][0]
                      ? "none"
                      : "1px solid #ece3d9",
                  fontSize: 14,
                  color: "#2b3734",
                }}
              >
                <span style={{ color: "#586a64", fontWeight: 500 }}>
                  {label}
                </span>
                <strong style={{ textAlign: "right" }}>{value}</strong>
              </div>
            ))}
          </div>
        </div>
      )}

      <div
        style={{
          marginTop: 18,
          color: "#66736d",
          fontSize: 12,
          wordBreak: "break-all",
          borderTop: "1px solid #e8dfd5",
          paddingTop: 12,
        }}
      >
        Fallback link: https://app.daymark.com/action/example-token
      </div>
    </EmailLayout>
  );
}

export const emailTemplateOptions = Object.entries(sample).map(
  ([key, value]) => ({
    key,
    label: value.title,
  }),
);

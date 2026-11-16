export function EmailLayout({
  eyebrow = "DAYMARK",
  title,
  children,
  action,
  disclaimer,
  footerNote = "This is an automated message from Daymark.",
}) {
  return (
    <div
      style={{
        background: "#eee8e2",
        minHeight: "100%",
        padding: "32px 16px",
        color: "#17211e",
        fontFamily: '"DM Sans", "Segoe UI", Arial, sans-serif',
      }}
    >
      <div
        style={{
          maxWidth: 700,
          margin: "0 auto",
          background: "#fffdf9",
          border: "1px solid rgba(23, 33, 30, 0.08)",
          borderRadius: 24,
          overflow: "hidden",
          boxShadow: "0 26px 52px rgba(23, 33, 30, 0.08)",
        }}
      >
        <header
          style={{
            background:
              "linear-gradient(135deg, #17211e 0%, #17211e 72%, #ff5c35 72%, #ff5c35 100%)",
            padding: "20px 28px 22px",
            color: "#fffaf4",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 16,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                fontWeight: 800,
                fontSize: 22,
                letterSpacing: "-0.06em",
              }}
            >
              <svg
                width="30"
                height="30"
                viewBox="0 0 32 32"
                role="img"
                aria-label="Daymark"
                style={{ display: "block" }}
              >
                <path
                  d="M6 5h10c6.1 0 10 3.8 10 11s-3.9 11-10 11H6V5Z"
                  fill="currentColor"
                />
                <path
                  d="M12 10h3.5c3 0 4.7 2.1 4.7 6s-1.7 6-4.7 6H12V10Z"
                  fill="#ff5c35"
                />
                <path d="M24 6.5 27.5 3 29 4.5 25.5 8 24 6.5Z" fill="#fffaf4" />
              </svg>
              <span>Daymark</span>
            </div>
            <div
              style={{
                fontSize: 10,
                letterSpacing: "0.18em",
                fontWeight: 700,
                textTransform: "uppercase",
                background: "rgba(255,255,255,0.09)",
                border: "1px solid rgba(255,255,255,0.15)",
                borderRadius: 999,
                padding: "8px 10px",
                whiteSpace: "nowrap",
              }}
            >
              {eyebrow}
            </div>
          </div>
        </header>

        <main style={{ padding: "28px 28px 0" }}>
          <div
            style={{
              margin: "0 0 12px",
              fontFamily: '"IBM Plex Mono", "SFMono-Regular", monospace',
              fontSize: 11,
              letterSpacing: "0.16em",
              textTransform: "uppercase",
              color: "#697772",
            }}
          >
            {eyebrow}
          </div>

          <h1
            style={{
              margin: "0 0 18px",
              fontSize: 36,
              lineHeight: 1.06,
              letterSpacing: "-0.07em",
              fontWeight: 600,
              color: "#17211e",
              fontFamily: '"Onest", "Segoe UI", sans-serif',
            }}
          >
            {title}
          </h1>

          <div style={{ paddingBottom: 10 }}>{children}</div>

          {action && <div style={{ marginTop: 22 }}>{action}</div>}

          {disclaimer && (
            <p
              style={{
                margin: "20px 0 0",
                color: "#66736d",
                fontSize: 12,
                lineHeight: 1.7,
              }}
            >
              {disclaimer}
            </p>
          )}
        </main>

        <footer
          style={{
            padding: "18px 28px 24px",
            borderTop: "1px solid #ece4db",
            color: "#61716b",
            fontSize: 12,
            lineHeight: 1.8,
            background: "#fffdf9",
          }}
        >
          Need help?{" "}
          <a
            href="mailto:support@daymark.app"
            style={{ color: "#17211e", fontWeight: 700 }}
          >
            support@daymark.app
          </a>
          <br />© Daymark · {footerNote}
        </footer>
      </div>
    </div>
  );
}

export function EmailText({ children }) {
  return (
    <p
      style={{
        margin: "0 0 16px",
        lineHeight: 1.75,
        color: "#2a3734",
        fontSize: 16,
      }}
    >
      {children}
    </p>
  );
}

export function EmailButton({ children }) {
  return (
    <a
      href="https://app.daymark.com"
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(180deg, #ff744d 0%, #ff5c35 100%)",
        color: "#fffaf4",
        padding: "15px 26px",
        fontWeight: 700,
        fontSize: 15,
        lineHeight: 1,
        textDecoration: "none",
        borderRadius: 999,
        border: "1px solid #eb4f2f",
        boxShadow: "0 14px 24px rgba(255, 92, 53, 0.18)",
      }}
    >
      {children}
    </a>
  );
}

import { useState } from "react";
import { Search, Status, Pagination } from "../../../app/application/Ui";

export function AdminHead({ label, title, copy, action }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-end",
        gap: "16px",
        marginBottom: "20px",
        flexWrap: "wrap",
      }}
    >
      <div>
        <span
          style={{
            display: "block",
            color: "#5d675f",
            letterSpacing: "0.12em",
            fontWeight: 700,
            fontSize: "12px",
          }}
        >
          {label}
        </span>
        <h1
          style={{
            margin: "8px 0 0",
            fontSize: "clamp(2rem, 3vw, 2.7rem)",
            letterSpacing: "-0.06em",
          }}
        >
          {title}
        </h1>
        <p style={{ margin: "10px 0 0", color: "#4a564f" }}>{copy}</p>
      </div>
      {action}
    </div>
  );
}

export function PanelHead({ title, copy, link }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "10px",
        marginBottom: "18px",
      }}
    >
      <div>
        <b style={{ display: "block" }}>{title}</b>
        <small style={{ color: "#5d675f" }}>{copy}</small>
      </div>
      {link && (
        <button
          style={{
            border: 0,
            background: "transparent",
            color: "#111917",
            fontWeight: 700,
          }}
        >
          {link} →
        </button>
      )}
    </div>
  );
}

export function EmailCentreShell({ title, subtitle, children, tabs = [] }) {
  return (
    <>
      <AdminHead
        label="PLATFORM COMMUNICATIONS"
        title={title}
        copy={subtitle}
        action={
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {tabs.map(([label, href]) => (
              <a
                key={href}
                href={href}
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "999px",
                  background: "#fff",
                  color: "#111917",
                  padding: "9px 12px",
                  fontWeight: 700,
                  textDecoration: "none",
                }}
              >
                {label}
              </a>
            ))}
          </div>
        }
      />
      {children}
    </>
  );
}

export function AdminTablePage({ type, rows, columns, description }) {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState(null);

  const filtered = rows.filter((row) =>
    row.join(" ").toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <>
      <AdminHead
        label={`PLATFORM / ${type.toUpperCase()}`}
        title={type}
        copy={description}
        action={
          type === "Businesses" ? (
            <button
              style={{
                background: "#111917",
                color: "#fff",
                border: 0,
                borderRadius: "12px",
                padding: "12px 16px",
                fontWeight: 700,
              }}
            >
              Export businesses
            </button>
          ) : undefined
        }
      />

      <div
        style={{
          background: "#fff",
          borderRadius: "22px",
          border: "1px solid rgba(17,25,23,0.04)",
          boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
          padding: "18px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "12px",
            marginBottom: "14px",
            flexWrap: "wrap",
          }}
        >
          <Search
            value={search}
            onChange={setSearch}
            placeholder={`Search ${type.toLowerCase()}`}
          />
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <select
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                background: "#fff",
                padding: "10px 12px",
              }}
            >
              <option>All statuses</option>
              <option>Active</option>
              <option>Suspended</option>
            </select>
            <button
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                background: "#f7f8f6",
                borderRadius: "12px",
                padding: "10px 12px",
                fontWeight: 700,
              }}
            >
              Filters
            </button>
          </div>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {columns.map((column) => (
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
                <th style={{ width: "20px" }} />
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr
                  key={row[0]}
                  style={{ borderTop: "1px solid rgba(17,25,23,0.06)" }}
                >
                  {row.map((cell, index) => (
                    <td
                      key={`${row[0]}-${index}`}
                      style={{ padding: "12px 8px", verticalAlign: "middle" }}
                    >
                      {index === 0 ? (
                        <button
                          onClick={() => setSelected(row)}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "10px",
                            border: 0,
                            background: "transparent",
                            padding: 0,
                            color: "#111917",
                            fontWeight: 700,
                          }}
                        >
                          <i
                            style={{
                              width: "30px",
                              height: "30px",
                              borderRadius: "50%",
                              background: "#eff1ee",
                              display: "inline-flex",
                              alignItems: "center",
                              justifyContent: "center",
                              fontSize: "11px",
                            }}
                          >
                            {cell
                              .split(" ")
                              .map((part) => part[0])
                              .join("")
                              .slice(0, 2)}
                          </i>
                          <span>{cell}</span>
                        </button>
                      ) : [
                          "Active",
                          "Suspended",
                          "Trial",
                          "Successful",
                          "Failed",
                        ].includes(cell) ? (
                        <Status>{cell}</Status>
                      ) : (
                        cell
                      )}
                    </td>
                  ))}
                  <td>
                    <button
                      style={{
                        border: 0,
                        background: "transparent",
                        fontSize: "1.4rem",
                        color: "#47514d",
                      }}
                    >
                      •••
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ marginTop: "20px" }}>
          <Pagination />
        </div>
      </div>

      {selected && (
        <AdminDrawer
          type={type}
          record={selected}
          close={() => setSelected(null)}
        />
      )}
    </>
  );
}

export function AdminDrawer({ type, record, close }) {
  const [suspended, setSuspended] = useState(record.includes("Suspended"));

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 40 }}>
      <button
        aria-label="Close record"
        onClick={close}
        style={{
          position: "absolute",
          inset: 0,
          border: 0,
          background: "rgba(17,25,23,0.3)",
        }}
      />
      <aside
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          height: "100%",
          width: "420px",
          background: "#fff",
          boxShadow: "-20px 0 30px rgba(17,25,23,0.08)",
          padding: "18px 20px",
          overflowY: "auto",
        }}
      >
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "18px",
          }}
        >
          <span
            style={{
              fontSize: "11px",
              letterSpacing: "0.12em",
              color: "#5d675f",
              fontWeight: 700,
            }}
          >
            {type.toUpperCase()} / RECORD
          </span>
          <button
            style={{ border: 0, background: "transparent", fontSize: "1.5rem" }}
            onClick={close}
          >
            ×
          </button>
        </header>

        <div
          style={{
            display: "grid",
            placeItems: "center",
            marginBottom: "16px",
          }}
        >
          <i
            style={{
              width: "54px",
              height: "54px",
              display: "grid",
              placeItems: "center",
              borderRadius: "50%",
              background: "#eff1ee",
              fontWeight: 800,
              fontSize: "1.2rem",
            }}
          >
            {record[0]
              .split(" ")
              .map((part) => part[0])
              .join("")
              .slice(0, 2)}
          </i>
          <h2 style={{ margin: "12px 0 4px", fontSize: "1.8rem" }}>
            {record[0]}
          </h2>
          <p style={{ margin: 0, color: "#5d675f" }}>{record[1]}</p>
        </div>

        <dl style={{ display: "grid", gap: "12px", margin: "0 0 18px" }}>
          {record.slice(2).map((item, index) => (
            <div
              key={`${item}-${index}`}
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: "20px",
                borderBottom: "1px solid rgba(17,25,23,0.08)",
                paddingBottom: "10px",
              }}
            >
              <dt style={{ color: "#5d675f", fontWeight: 600 }}>
                Record detail {index + 1}
              </dt>
              <dd style={{ margin: 0, fontWeight: 600, textAlign: "right" }}>
                {item}
              </dd>
            </div>
          ))}
        </dl>

        {type === "Businesses" && (
          <>
            <div
              style={{
                border: "1px solid rgba(17,25,23,0.08)",
                borderRadius: "16px",
                padding: "12px 14px",
                background: "#f7f8f6",
              }}
            >
              <b style={{ display: "block" }}>Platform controls</b>
              <p style={{ margin: "8px 0 0", color: "#5d675f" }}>
                Suspending prevents access to the organization without deleting
                its business data.
              </p>
            </div>
            <button
              style={{
                width: "100%",
                marginTop: "18px",
                border: 0,
                background: suspended ? "#1c3f33" : "#ef4d2f",
                color: "#fff",
                padding: "12px 14px",
                borderRadius: "12px",
                fontWeight: 800,
              }}
              onClick={() => setSuspended(!suspended)}
            >
              {suspended ? "Reactivate business" : "Suspend business"}
            </button>
          </>
        )}

        <p style={{ marginTop: "18px", color: "#5d675f" }}>
          Actions require confirmation from the platform API before the status
          is changed.
        </p>
      </aside>
    </div>
  );
}

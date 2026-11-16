import { AdminHead } from "../../components/AdminShell";

export function FeatureFlags() {
  return (
    <>
      <AdminHead
        label="CONTROL CENTRE"
        title="Feature Flags"
        copy="Enable or disable product capabilities across environments and tenant cohorts."
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
          Feature flag configuration will be connected to the platform settings
          layer in the next release.
        </p>
      </div>
    </>
  );
}

export function SecurityAccess() {
  return (
    <>
      <AdminHead
        label="ACCESS MANAGEMENT"
        title="Security & Access"
        copy="Review platform role policies, authentication posture and administrative controls."
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
          Platform security controls are enforced server-side and are ready for
          role expansion.
        </p>
      </div>
    </>
  );
}

export function Backups() {
  return (
    <>
      <AdminHead
        label="INFRASTRUCTURE"
        title="Backup Monitoring"
        copy="Monitor backup integrity, retention and restore readiness for the Daymark platform."
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
          Backup and restore monitoring is available as the platform operations
          layer matures.
        </p>
      </div>
    </>
  );
}

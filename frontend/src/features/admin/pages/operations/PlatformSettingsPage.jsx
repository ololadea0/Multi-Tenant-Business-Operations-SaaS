import { useEffect, useState } from "react";
import {
  usePlatformSettingsQuery,
  useUpdatePlatformSettingsMutation,
} from "../../../../app/store/api";
import { AdminHead } from "../../components/AdminShell";

export function PlatformSettings() {
  const { data: settings, isLoading, refetch } = usePlatformSettingsQuery();
  const [updatePlatformSettings, { isLoading: saving }] =
    useUpdatePlatformSettingsMutation();
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({
    trial_duration_days: 14,
    trial_enabled: true,
    trial_plan_key: "growth",
    billing_intervals: ["monthly", "annual"],
    renewal_policy: "manual",
    annual_billing_discount_percent: 15,
    payment_grace_period_days: 3,
    support_email: "support@daymark.app",
    support_phone: "+234 800 000 0000",
    help_center_url: "https://help.daymark.app",
    allow_new_registrations: true,
    maintenance_notice_enabled: false,
    maintenance_message:
      "Scheduled maintenance is in progress. Please check back shortly.",
    maintenance_until: "",
  });

  useEffect(() => {
    if (settings) {
      setForm((current) => ({
        ...current,
        ...settings,
        maintenance_message:
          settings.maintenance_message ||
          "Scheduled maintenance is in progress. Please check back shortly.",
        maintenance_until: settings.maintenance_until || "",
      }));
    }
  }, [settings]);

  async function save(event) {
    event.preventDefault();
    const payload = {
      ...form,
      trial_plan_key: String(form.trial_plan_key || "growth")
        .trim()
        .toLowerCase(),
      billing_intervals: Array.isArray(form.billing_intervals)
        ? form.billing_intervals
        : ["monthly", "annual"],
      renewal_policy: String(form.renewal_policy || "manual")
        .trim()
        .toLowerCase(),
      maintenance_until: form.maintenance_until
        ? new Date(form.maintenance_until).toISOString()
        : null,
    };

    const savedSettings = await updatePlatformSettings(payload).unwrap();
    setForm((current) => ({
      ...current,
      ...savedSettings,
      billing_intervals: Array.isArray(savedSettings.billing_intervals)
        ? savedSettings.billing_intervals
        : ["monthly", "annual"],
      maintenance_until: savedSettings.maintenance_until || "",
    }));
    await refetch();
    setSaved(true);
  }

  return (
    <>
      <AdminHead
        label="PLATFORM CONFIGURATION"
        title="Platform Settings"
        copy="Manage defaults that affect Daymark customers and commercial operations."
      />

      {isLoading && (
        <p style={{ margin: "0 0 20px", color: "#59655f" }}>
          Loading platform settings...
        </p>
      )}

      <form onSubmit={save} style={{ display: "grid", gap: "18px" }}>
        {saved && (
          <div
            style={{
              background: "#eaf9ee",
              color: "#0f5b32",
              borderRadius: "12px",
              padding: "12px 14px",
              border: "1px solid rgba(13,108,61,0.12)",
            }}
          >
            Platform settings were saved successfully.
          </div>
        )}

        <section
          style={{
            background: "#fff",
            borderRadius: "20px",
            padding: "20px",
            border: "1px solid rgba(17,25,23,0.04)",
            boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
          }}
        >
          <header style={{ marginBottom: "16px" }}>
            <h2 style={{ margin: 0 }}>Trials and billing</h2>
            <p style={{ margin: "8px 0 0", color: "#5d675f" }}>
              Defaults for new customer subscriptions.
            </p>
          </header>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
              gap: "16px",
            }}
          >
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Trial duration
              <input
                type="number"
                value={form.trial_duration_days}
                onChange={(event) =>
                  setForm({
                    ...form,
                    trial_duration_days: Number(event.target.value),
                  })
                }
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              />
              <small style={{ color: "#5d675f" }}>Days</small>
            </label>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Trial plan key
              <input
                value={form.trial_plan_key}
                onChange={(event) =>
                  setForm({
                    ...form,
                    trial_plan_key: event.target.value,
                  })
                }
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              />
            </label>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Renewal policy
              <select
                value={form.renewal_policy}
                onChange={(event) =>
                  setForm({
                    ...form,
                    renewal_policy: event.target.value,
                  })
                }
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              >
                <option value="manual">Manual</option>
                <option value="automatic">Automatic</option>
              </select>
            </label>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Annual billing discount
              <input
                type="number"
                value={form.annual_billing_discount_percent}
                onChange={(event) =>
                  setForm({
                    ...form,
                    annual_billing_discount_percent: Number(event.target.value),
                  })
                }
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              />
              <small style={{ color: "#5d675f" }}>Percent</small>
            </label>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Payment grace period
              <input
                type="number"
                value={form.payment_grace_period_days}
                onChange={(event) =>
                  setForm({
                    ...form,
                    payment_grace_period_days: Number(event.target.value),
                  })
                }
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              />
              <small style={{ color: "#5d675f" }}>Days</small>
            </label>
            <div style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Billing intervals
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {[
                  { value: "monthly", label: "Monthly" },
                  { value: "annual", label: "Annual" },
                ].map((interval) => {
                  const checked = form.billing_intervals.includes(
                    interval.value,
                  );
                  return (
                    <label
                      key={interval.value}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "8px",
                        border: "1px solid rgba(17,25,23,0.12)",
                        borderRadius: "10px",
                        padding: "9px 10px",
                        background: checked ? "#f2f7f4" : "#fff",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() =>
                          setForm((current) => {
                            const next = new Set(
                              current.billing_intervals || [],
                            );
                            if (next.has(interval.value))
                              next.delete(interval.value);
                            else next.add(interval.value);
                            return {
                              ...current,
                              billing_intervals: Array.from(next),
                            };
                          })
                        }
                      />
                      {interval.label}
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <section
          style={{
            background: "#fff",
            borderRadius: "20px",
            padding: "20px",
            border: "1px solid rgba(17,25,23,0.04)",
            boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
          }}
        >
          <header style={{ marginBottom: "16px" }}>
            <h2 style={{ margin: 0 }}>Support details</h2>
            <p style={{ margin: "8px 0 0", color: "#5d675f" }}>
              Contact information shown to Daymark customers.
            </p>
          </header>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: "16px",
            }}
          >
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Support email
              <input
                type="email"
                value={form.support_email}
                onChange={(event) =>
                  setForm({ ...form, support_email: event.target.value })
                }
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              />
            </label>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Support phone
              <input
                value={form.support_phone}
                onChange={(event) =>
                  setForm({ ...form, support_phone: event.target.value })
                }
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              />
            </label>
            <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
              Help centre URL
              <input
                value={form.help_center_url}
                onChange={(event) =>
                  setForm({ ...form, help_center_url: event.target.value })
                }
                style={{
                  border: "1px solid rgba(17,25,23,0.12)",
                  borderRadius: "12px",
                  padding: "11px 12px",
                }}
              />
            </label>
          </div>
        </section>

        <section
          style={{
            background: "#fff",
            borderRadius: "20px",
            padding: "20px",
            border: "1px solid rgba(17,25,23,0.04)",
            boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
          }}
        >
          <header style={{ marginBottom: "16px" }}>
            <h2 style={{ margin: 0 }}>Platform access</h2>
            <p style={{ margin: "8px 0 0", color: "#5d675f" }}>
              Control customer-facing platform availability.
            </p>
          </header>
          <div style={{ display: "grid", gap: "16px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "20px",
                border: "1px solid rgba(17,25,23,0.08)",
                borderRadius: "14px",
                padding: "14px 16px",
              }}
            >
              <div>
                <b style={{ display: "block" }}>Trial access</b>
                <small style={{ color: "#5d675f" }}>
                  Enable or disable the platform trial flow for new accounts.
                </small>
              </div>
              <button
                type="button"
                onClick={() =>
                  setForm({
                    ...form,
                    trial_enabled: !form.trial_enabled,
                  })
                }
                style={{
                  border: 0,
                  background: form.trial_enabled ? "#1c3f33" : "#e6e8e4",
                  borderRadius: "999px",
                  width: "54px",
                  height: "28px",
                  position: "relative",
                  cursor: "pointer",
                }}
              >
                <i
                  style={{
                    position: "absolute",
                    right: form.trial_enabled ? "6px" : "auto",
                    left: form.trial_enabled ? "auto" : "6px",
                    top: "5px",
                    width: "18px",
                    height: "18px",
                    borderRadius: "50%",
                    background: "#fff",
                    display: "block",
                  }}
                />
              </button>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "20px",
                border: "1px solid rgba(17,25,23,0.08)",
                borderRadius: "14px",
                padding: "14px 16px",
              }}
            >
              <div>
                <b style={{ display: "block" }}>Allow new registrations</b>
                <small style={{ color: "#5d675f" }}>
                  New customers can create Daymark accounts.
                </small>
              </div>
              <button
                type="button"
                onClick={() =>
                  setForm({
                    ...form,
                    allow_new_registrations: !form.allow_new_registrations,
                  })
                }
                style={{
                  border: 0,
                  background: form.allow_new_registrations
                    ? "#1c3f33"
                    : "#e6e8e4",
                  borderRadius: "999px",
                  width: "54px",
                  height: "28px",
                  position: "relative",
                  cursor: "pointer",
                }}
              >
                <i
                  style={{
                    position: "absolute",
                    right: form.allow_new_registrations ? "6px" : "auto",
                    left: form.allow_new_registrations ? "auto" : "6px",
                    top: "5px",
                    width: "18px",
                    height: "18px",
                    borderRadius: "50%",
                    background: "#fff",
                    display: "block",
                  }}
                />
              </button>
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: "20px",
                border: "1px solid rgba(17,25,23,0.08)",
                borderRadius: "14px",
                padding: "14px 16px",
              }}
            >
              <div style={{ flex: 1 }}>
                <b style={{ display: "block" }}>Maintenance notice</b>
                <small style={{ color: "#5d675f" }}>
                  Show a non-blocking notice across customer workspaces.
                </small>
                <div
                  style={{ display: "grid", gap: "10px", marginTop: "12px" }}
                >
                  <textarea
                    value={form.maintenance_message}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        maintenance_message: event.target.value,
                      })
                    }
                    rows={3}
                    placeholder="Maintenance banner message"
                    style={{
                      border: "1px solid rgba(17,25,23,0.12)",
                      borderRadius: "12px",
                      padding: "10px 12px",
                      resize: "vertical",
                    }}
                  />
                  <label
                    style={{ display: "grid", gap: "8px", fontWeight: 700 }}
                  >
                    Maintenance ends by
                    <input
                      type="datetime-local"
                      value={
                        form.maintenance_until
                          ? form.maintenance_until.slice(0, 16)
                          : ""
                      }
                      onChange={(event) =>
                        setForm({
                          ...form,
                          maintenance_until: event.target.value,
                        })
                      }
                      style={{
                        border: "1px solid rgba(17,25,23,0.12)",
                        borderRadius: "12px",
                        padding: "11px 12px",
                      }}
                    />
                  </label>
                </div>
              </div>
              <button
                type="button"
                onClick={() =>
                  setForm({
                    ...form,
                    maintenance_notice_enabled:
                      !form.maintenance_notice_enabled,
                  })
                }
                style={{
                  border: 0,
                  background: form.maintenance_notice_enabled
                    ? "#1c3f33"
                    : "#e6e8e4",
                  borderRadius: "999px",
                  width: "54px",
                  height: "28px",
                  position: "relative",
                  cursor: "pointer",
                }}
              >
                <i
                  style={{
                    position: "absolute",
                    right: form.maintenance_notice_enabled ? "6px" : "auto",
                    left: form.maintenance_notice_enabled ? "auto" : "6px",
                    top: "5px",
                    width: "18px",
                    height: "18px",
                    borderRadius: "50%",
                    background: "#fff",
                    display: "block",
                  }}
                />
              </button>
            </div>
          </div>
        </section>

        <footer style={{ display: "flex", justifyContent: "flex-end" }}>
          <button
            type="submit"
            disabled={saving}
            style={{
              border: 0,
              background: "#111917",
              color: "#fff",
              borderRadius: "12px",
              padding: "12px 18px",
              fontWeight: 700,
              opacity: saving ? 0.7 : 1,
            }}
          >
            {saving ? "Saving..." : "Save platform settings"}
          </button>
        </footer>
      </form>
    </>
  );
}

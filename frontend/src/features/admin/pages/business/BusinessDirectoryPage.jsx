import { useState } from "react";
import {
  useAdminDashboardQuery,
  usePlansQuery,
  useUpdatePlanMutation,
  useCreatePlanMutation,
} from "../../../../app/store/api";
import { Icon, Status } from "../../../../app/application/Ui";
import { AdminHead, AdminTablePage } from "../../components/AdminShell";

export const Businesses = () => {
  const { data } = useAdminDashboardQuery();
  const rows = (data?.businesses ?? []).map((business) => [
    business.name,
    business.owner_email ?? "—",
    business.plan ?? "Starter",
    business.status ?? "Active",
    String(business.users ?? 0),
    business.created_at ?? "—",
  ]);

  return (
    <AdminTablePage
      type="Businesses"
      rows={rows}
      columns={[
        "Business",
        "Owner email",
        "Plan",
        "Status",
        "Users",
        "Created",
      ]}
      description="View, search and control customer organizations across Daymark."
    />
  );
};

export const Users = () => {
  const { data } = useAdminDashboardQuery();
  const rows = (data?.users ?? []).map((user) => [
    user.full_name,
    user.email,
    String(user.businesses ?? 0),
    user.status ?? "Active",
    user.sign_in ?? "Password",
    user.last_active ?? "Never",
  ]);

  return (
    <AdminTablePage
      type="Users"
      rows={rows}
      columns={[
        "User",
        "Email",
        "Businesses",
        "Status",
        "Sign-in",
        "Last active",
      ]}
      description="Review registered users and their account status."
    />
  );
};

export const Subscriptions = () => {
  const { data } = useAdminDashboardQuery();
  const rows = (data?.subscriptions ?? []).map((subscription) => [
    subscription.business_name,
    subscription.plan ?? "Starter",
    subscription.billing_interval
      ? subscription.billing_interval.charAt(0).toUpperCase() +
        subscription.billing_interval.slice(1)
      : "Monthly",
    subscription.status ?? "Active",
    subscription.amount ?? "₦0",
    subscription.renewal ?? "—",
  ]);

  return (
    <AdminTablePage
      type="Subscriptions"
      rows={rows}
      columns={["Business", "Plan", "Cycle", "Status", "Amount", "Renewal"]}
      description="Manage trials, upgrades, cancellations and subscription suspensions."
    />
  );
};

export const Payments = () => {
  const { data } = useAdminDashboardQuery();
  const rows = (data?.payments ?? []).map((payment) => [
    payment.reference,
    payment.business_name,
    payment.amount ?? "₦0",
    payment.status ?? "Pending",
    payment.provider ?? "Paystack",
    payment.created_at ?? "—",
  ]);

  return (
    <AdminTablePage
      type="Payments"
      rows={rows}
      columns={[
        "Reference",
        "Business",
        "Amount",
        "Status",
        "Provider",
        "Date",
      ]}
      description="Inspect Paystack transaction references and platform payment history."
    />
  );
};

export function Plans() {
  const [editing, setEditing] = useState(null);
  const { data: plans = [], isLoading } = usePlansQuery();

  const formatNaira = (value) =>
    new Intl.NumberFormat("en-NG", {
      style: "currency",
      currency: "NGN",
      maximumFractionDigits: 0,
    }).format(value || 0);

  return (
    <>
      <AdminHead
        label="COMMERCIAL SETTINGS"
        title="Plans & Pricing"
        copy="Create plans, edit prices and configure limits shown to Daymark customers."
        action={
          <button
            type="button"
            onClick={() =>
              setEditing({
                newPlan: true,
                key: "",
                name: "",
                description: "",
                monthly_price: 0,
                annual_price: 0,
                max_team_members: 1,
                max_products: 10,
                max_monthly_orders: 20,
              })
            }
            style={{
              background: "#111917",
              color: "#fff",
              border: 0,
              borderRadius: "12px",
              padding: "12px 16px",
              fontWeight: 700,
            }}
          >
            Create plan
          </button>
        }
      />

      {isLoading && (
        <p style={{ margin: "0 0 18px", color: "#59655f" }}>
          Loading plan pricing...
        </p>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "18px",
        }}
      >
        {plans.map((plan, index) => (
          <article
            key={plan.key}
            style={{
              background: "#fff",
              borderRadius: "20px",
              border: "1px solid rgba(17,25,23,0.06)",
              padding: "18px",
              boxShadow: "0 8px 22px rgba(17,25,23,0.04)",
            }}
          >
            <header
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "10px",
              }}
            >
              <span
                style={{
                  color: "#5d675f",
                  fontSize: "11px",
                  letterSpacing: "0.12em",
                  fontWeight: 700,
                }}
              >
                PLAN 0{index + 1}
              </span>
              <Status />
            </header>
            <h2 style={{ margin: "18px 0 8px", fontSize: "2rem" }}>
              {plan.name}
            </h2>
            <strong
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: "6px",
                fontSize: "2rem",
              }}
            >
              {formatNaira(plan.monthly_price)}
              <small style={{ fontSize: "0.86rem", color: "#5d675f" }}>
                / month
              </small>
            </strong>
            <p style={{ color: "#586863", margin: "12px 0 18px" }}>
              {plan.description}
            </p>
            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: "0 0 18px",
                display: "grid",
                gap: "8px",
              }}
            >
              {[
                `Up to ${plan.max_team_members} team members`,
                `Up to ${plan.max_products} products`,
                `Up to ${plan.max_monthly_orders} orders per month`,
              ].map((detail) => (
                <li
                  key={detail}
                  style={{ display: "flex", alignItems: "center", gap: "8px" }}
                >
                  <Icon name="plus" /> <span>{detail}</span>
                </li>
              ))}
            </ul>
            <button
              onClick={() => setEditing(plan)}
              style={{
                width: "100%",
                border: "1px solid rgba(17,25,23,0.12)",
                background: "#f7f8f6",
                borderRadius: "12px",
                padding: "11px 12px",
                fontWeight: 700,
              }}
            >
              Edit plan
            </button>
          </article>
        ))}
      </div>

      {editing && <PlanDialog plan={editing} close={() => setEditing(null)} />}
    </>
  );
}

function PlanDialog({ plan, close }) {
  const [updatePlan, { isLoading: saving }] = useUpdatePlanMutation();
  const [createPlan, { isLoading: creating }] = useCreatePlanMutation();

  async function handleSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = {
      name: String(formData.get("name") || "").trim(),
      description: String(formData.get("description") || "").trim(),
      monthly_price: Number(formData.get("monthly_price") || 0),
      annual_price: Number(formData.get("annual_price") || 0),
      currency: "NGN",
      max_team_members: Number(formData.get("max_team_members") || 0),
      max_products: Number(formData.get("max_products") || 0),
      max_monthly_orders: Number(formData.get("max_monthly_orders") || 0),
      is_active: formData.get("is_active") === "on",
      display_order: Number(formData.get("display_order") || 0),
    };

    if (plan.newPlan) {
      payload.key = String(formData.get("key") || "")
        .trim()
        .toLowerCase();
      await createPlan(payload).unwrap();
    } else {
      await updatePlan({ plan_key: plan.key, ...payload }).unwrap();
    }
    close();
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 40,
        display: "grid",
        placeItems: "center",
      }}
    >
      <button
        aria-label="Close dialog"
        onClick={close}
        style={{
          position: "absolute",
          inset: 0,
          border: 0,
          background: "rgba(17,25,23,0.3)",
        }}
      />
      <form
        onSubmit={handleSubmit}
        style={{
          position: "relative",
          width: "min(560px, calc(100vw - 32px))",
          background: "#fff",
          borderRadius: "22px",
          padding: "18px",
          boxShadow: "0 20px 40px rgba(17,25,23,0.12)",
        }}
      >
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "12px",
            marginBottom: "18px",
          }}
        >
          <div>
            <span
              style={{
                color: "#5d675f",
                letterSpacing: "0.12em",
                fontSize: "11px",
                fontWeight: 700,
              }}
            >
              PLAN CONFIGURATION
            </span>
            <h2 style={{ margin: "8px 0 0" }}>
              {plan.newPlan ? "Create plan" : `Edit ${plan.name}`}
            </h2>
          </div>
          <button
            type="button"
            onClick={close}
            style={{ border: 0, background: "transparent", fontSize: "1.6rem" }}
          >
            ×
          </button>
        </header>

        <label
          style={{
            display: "grid",
            gap: "8px",
            marginBottom: "12px",
            fontWeight: 700,
          }}
        >
          {plan.newPlan && "Plan key"}
          {plan.newPlan && (
            <input
              name="key"
              placeholder="e.g. growth"
              required
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                padding: "11px 12px",
                fontSize: "1rem",
              }}
            />
          )}
          Plan name
          <input
            name="name"
            defaultValue={plan.name || ""}
            style={{
              border: "1px solid rgba(17,25,23,0.12)",
              borderRadius: "12px",
              padding: "11px 12px",
              fontSize: "1rem",
            }}
          />
        </label>

        <label
          style={{
            display: "grid",
            gap: "8px",
            marginBottom: "12px",
            fontWeight: 700,
          }}
        >
          Plan description
          <textarea
            name="description"
            defaultValue={plan.description}
            rows={3}
            style={{
              border: "1px solid rgba(17,25,23,0.12)",
              borderRadius: "12px",
              padding: "11px 12px",
              resize: "vertical",
            }}
          />
        </label>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            gap: "12px",
            marginBottom: "12px",
          }}
        >
          <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
            Monthly price (₦)
            <input
              name="monthly_price"
              type="number"
              defaultValue={plan.monthly_price ?? 0}
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                padding: "11px 12px",
              }}
            />
          </label>
          <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
            Annual price (₦)
            <input
              name="annual_price"
              type="number"
              defaultValue={plan.annual_price ?? 0}
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                padding: "11px 12px",
              }}
            />
          </label>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: "12px",
            marginBottom: "18px",
          }}
        >
          <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
            Team members
            <input
              name="max_team_members"
              type="number"
              defaultValue={plan.max_team_members ?? 0}
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                padding: "11px 12px",
              }}
            />
          </label>
          <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
            Products
            <input
              name="max_products"
              type="number"
              defaultValue={plan.max_products ?? 0}
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                padding: "11px 12px",
              }}
            />
          </label>
          <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
            Monthly orders
            <input
              name="max_monthly_orders"
              type="number"
              defaultValue={plan.max_monthly_orders ?? 0}
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                padding: "11px 12px",
              }}
            />
          </label>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            gap: "12px",
            marginBottom: "18px",
          }}
        >
          <label style={{ display: "grid", gap: "8px", fontWeight: 700 }}>
            Display order
            <input
              name="display_order"
              type="number"
              defaultValue={plan.display_order ?? 0}
              style={{
                border: "1px solid rgba(17,25,23,0.12)",
                borderRadius: "12px",
                padding: "11px 12px",
              }}
            />
          </label>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "10px",
              padding: "11px 12px",
              border: "1px solid rgba(17,25,23,0.12)",
              borderRadius: "12px",
              fontWeight: 700,
            }}
          >
            Active
            <input
              name="is_active"
              type="checkbox"
              defaultChecked={plan.is_active ?? true}
              style={{ width: "18px", height: "18px" }}
            />
          </label>
        </div>

        <div
          style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}
        >
          <button
            type="button"
            onClick={close}
            style={{
              border: "1px solid rgba(17,25,23,0.12)",
              background: "#fff",
              borderRadius: "12px",
              padding: "11px 16px",
              fontWeight: 700,
            }}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            style={{
              border: 0,
              background: "#111917",
              color: "#fff",
              borderRadius: "12px",
              padding: "11px 16px",
              fontWeight: 700,
            }}
          >
            {saving || creating
              ? "Saving..."
              : plan.newPlan
                ? "Create plan"
                : "Save changes"}
          </button>
        </div>
      </form>
    </div>
  );
}

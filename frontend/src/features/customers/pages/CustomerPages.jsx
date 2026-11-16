import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router";
import { money } from "../../../app/store/format";
import { useOrganizationData } from "../../../app/store/dataHooks";
import {
  EmptyState,
  Icon,
  Notice,
  PageHeader,
  Pagination,
  Search,
  Status,
} from "../../../app/application/Ui";
import {
  useCreateCustomerMutation,
  useCreateInventoryMovementMutation,
  useCreateOrderMutation,
  useCreateProductMutation,
  useUpdateProductMutation,
  useUpdateCustomerMutation,
  useCompleteOrderMutation,
  useCancelOrderMutation,
  useOrganizationQuery,
} from "../../../app/store/api";

function formatCustomerDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-NG", {
    timeZone: "Africa/Lagos",
    dateStyle: "medium",
  }).format(date);
}

function Toolbar({ search, setSearch, placeholder, children }) {
  return (
    <div className="record-toolbar">
      <Search value={search} onChange={setSearch} placeholder={placeholder} />
      <div>{children}</div>
    </div>
  );
}

export function Customers() {
  const { customers } = useOrganizationData();
  const [search, setSearch] = useState("");
  const { organizationId = "northstar" } = useParams();
  const navigate = useNavigate();
  const base = `/app/${organizationId}`;
  const rows = customers.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <>
      <PageHeader
        eyebrow="RELATIONSHIPS"
        title="Customers"
        description="Keep customer details and order history easy to reach."
        action={
          <Link className="app-btn primary" to={`${base}/customers/new`}>
            <Icon name="plus" />
            Add customer
          </Link>
        }
      />
      <div className="record-surface">
        <Toolbar
          search={search}
          setSearch={setSearch}
          placeholder="Search name, email or phone"
        />
        <div className="app-table-wrap">
          <table className="app-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Orders</th>
                <th>Date added</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr
                  key={c.id}
                  role="link"
                  tabIndex={0}
                  onClick={(event) => {
                    if (event.target.closest("a,button,input,select,textarea"))
                      return;
                    navigate(`${base}/customers/${c.id}`);
                  }}
                  onKeyDown={(event) => {
                    if (
                      (event.key === "Enter" || event.key === " ") &&
                      !event.target.closest("a,button,input,select,textarea")
                    ) {
                      event.preventDefault();
                      navigate(`${base}/customers/${c.id}`);
                    }
                  }}
                >
                  <td>
                    <Link
                      className="primary-cell"
                      to={`${base}/customers/${c.id}`}
                    >
                      <i>
                        {c.name
                          .split(" ")
                          .map((x) => x[0])
                          .join("")
                          .slice(0, 2)}
                      </i>
                      <b>{c.name}</b>
                    </Link>
                  </td>
                  <td>{c.email}</td>
                  <td>{c.phone}</td>
                  <td>{c.orders}</td>
                  <td>{c.added || c.joined || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Pagination />
      </div>
    </>
  );
}

export function CustomerForm() {
  const { customers } = useOrganizationData();
  const { organizationId, customerId } = useParams();
  const customer = customers.find(
    (item) => String(item.id) === String(customerId),
  );
  const isEditing = Boolean(customerId);

  return (
    <SimpleRecordForm
      title={isEditing ? "Edit customer" : "Add a customer"}
      eyebrow={isEditing ? "CUSTOMERS / EDIT" : "CUSTOMERS / NEW"}
      description={
        isEditing
          ? "Update the customer record and any contact details."
          : "Create a customer record for orders and contact history"
      }
      customer={customer}
      isEditing={isEditing}
      fields={["Customer name", "Email address", "Phone number"]}
    />
  );
}

function FormSection({ title, copy, children }) {
  return (
    <section className="form-section">
      <header>
        <h2>{title}</h2>
        <p>{copy}</p>
      </header>
      <div>{children}</div>
    </section>
  );
}

function SimpleRecordForm({
  title,
  eyebrow,
  description,
  fields,
  customer,
  isEditing,
}) {
  const nav = useNavigate();
  const { organizationId } = useParams();
  const [createCustomer, createState] = useCreateCustomerMutation();
  const [updateCustomer, updateState] = useUpdateCustomerMutation();
  const saveState = isEditing ? updateState : createState;

  async function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = {
      name: form.get("name"),
      email: form.get("email") || null,
      phone: form.get("phone") || null,
    };
    try {
      if (isEditing) {
        await updateCustomer({
          organizationId,
          customerId: customer.id,
          ...payload,
        }).unwrap();
      } else {
        await createCustomer({ organizationId, ...payload }).unwrap();
      }
      nav(`/app/${organizationId}/customers`);
    } catch {}
  }
  return (
    <>
      <PageHeader eyebrow={eyebrow} title={title} description={description} />
      <form className="single-form" onSubmit={submit}>
        <FormSection
          title="Contact information"
          copy="Add the details your team needs to identify and contact this customer."
        >
          {fields.map((x, i) => (
            <label key={x}>
              {x} {i === 0 && <em>Required</em>}
              <input
                name={i === 0 ? "name" : i === 1 ? "email" : "phone"}
                required={i === 0}
                type={x.includes("Email") ? "email" : "text"}
                defaultValue={
                  i === 0
                    ? customer?.name || ""
                    : i === 1
                      ? customer?.email || ""
                      : customer?.phone || ""
                }
              />
            </label>
          ))}
        </FormSection>
        <footer>
          <button
            className="app-btn secondary"
            type="button"
            onClick={() => nav(-1)}
          >
            Cancel
          </button>
          <button className="app-btn primary" disabled={saveState.isLoading}>
            {saveState.isLoading
              ? isEditing
                ? "Updating…"
                : "Saving…"
              : isEditing
                ? "Update customer"
                : "Save customer"}
          </button>
          {saveState.error && (
            <Notice tone="error">
              {saveState.error?.data?.detail || "Customer could not be saved."}
            </Notice>
          )}
        </footer>
      </form>
    </>
  );
}

export function CustomerDetails() {
  const { customers, orders } = useOrganizationData();
  const { organizationId = "northstar", customerId } = useParams();
  const c = customers.find((x) => String(x.id) === String(customerId)) ?? null;
  const base = `/app/${organizationId}`;

  if (!c) {
    return (
      <EmptyState
        title="Customer not found"
        copy="This customer is not available in the current workspace."
        to={`${base}/customers`}
      />
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="CUSTOMER RECORD"
        title={c.name}
        description={`Customer since ${c.added || c.joined || formatCustomerDate(c.created_at)}`}
        action={
          <Link
            className="app-btn primary"
            to={`${base}/customers/${c.id}/edit`}
          >
            Edit customer
          </Link>
        }
      />
      <div className="detail-grid">
        <section className="detail-main">
          <div className="detail-block">
            <h2>Contact details</h2>
            <dl>
              <div>
                <dt>Email</dt>
                <dd>{c.email}</dd>
              </div>
              <div>
                <dt>Phone</dt>
                <dd>{c.phone}</dd>
              </div>
              <div>
                <dt>Total orders</dt>
                <dd>{c.orders}</dd>
              </div>
              <div>
                <dt>Last order</dt>
                <dd>
                  {c.created_at
                    ? new Date(c.created_at).toLocaleDateString()
                    : "—"}
                </dd>
              </div>
            </dl>
          </div>
          <div className="detail-block">
            <div className="panel-heading">
              <div>
                <span>Order history</span>
                <small>Recent orders for this customer</small>
              </div>
              <Link to={`${base}/orders`}>View all →</Link>
            </div>
            {orders.slice(0, 3).map((o) => (
              <Link
                className="detail-event"
                to={`${base}/orders/${o.id}`}
                key={o.id}
              >
                <b>{o.number}</b>
                <span>
                  <b>{o.date}</b>
                  <small>{o.status}</small>
                </span>
                <em>{money(o.amount)}</em>
              </Link>
            ))}
          </div>
        </section>
        <aside className="customer-note">
          <span>INTERNAL NOTE</span>
          <p>Key wholesale account. Prefers consolidated weekly fulfilment.</p>
          <button>Add a note</button>
        </aside>
      </div>
    </>
  );
}

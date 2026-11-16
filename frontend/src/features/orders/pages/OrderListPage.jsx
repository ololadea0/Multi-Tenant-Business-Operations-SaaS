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
  useCompleteOrderMutation,
  useCancelOrderMutation,
  useOrganizationQuery,
} from "../../../app/store/api";

function Toolbar({ search, setSearch, placeholder, children }) {
  return (
    <div className="record-toolbar">
      <Search value={search} onChange={setSearch} placeholder={placeholder} />
      <div>{children}</div>
    </div>
  );
}

export function Orders() {
  const { orders } = useOrganizationData();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const { organizationId = "northstar" } = useParams();
  const navigate = useNavigate();
  const base = `/app/${organizationId}`;
  const customerLabel = (customer) => {
    if (customer && typeof customer === "object")
      return (
        customer.name || customer.email || `Customer #${customer.id || "—"}`
      );
    return customer ? String(customer) : "Customer —";
  };
  const rows = orders.filter(
    (o) =>
      (filter === "All" || o.status === filter) &&
      customerLabel(o.customer).toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <>
      <PageHeader
        eyebrow="ORDER MANAGEMENT"
        title="Orders"
        description="Track every order from creation through completion."
        action={
          <Link className="app-btn primary" to={`${base}/orders/new`}>
            <Icon name="plus" />
            Create order
          </Link>
        }
      />
      <div className="record-surface">
        <Toolbar
          search={search}
          setSearch={setSearch}
          placeholder="Search order or customer"
        >
          <div className="filter-tabs">
            {["All", "PENDING", "CONFIRMED", "COMPLETED", "CANCELLED"].map(
              (x) => (
                <button
                  className={filter === x ? "active" : ""}
                  onClick={() => setFilter(x)}
                  key={x}
                >
                  {x}
                </button>
              ),
            )}
          </div>
        </Toolbar>
        <div className="app-table-wrap">
          <table className="app-table">
            <thead>
              <tr>
                <th>Order</th>
                <th>Customer</th>
                <th>Order date</th>
                <th>Total</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((o) => (
                <tr
                  key={o.id}
                  role="link"
                  tabIndex={0}
                  onClick={(event) => {
                    if (event.target.closest("a,button,input,select,textarea"))
                      return;
                    navigate(`${base}/orders/${o.id}`);
                  }}
                  onKeyDown={(event) => {
                    if (
                      (event.key === "Enter" || event.key === " ") &&
                      !event.target.closest("a,button,input,select,textarea")
                    ) {
                      event.preventDefault();
                      navigate(`${base}/orders/${o.id}`);
                    }
                  }}
                >
                  <td>
                    <Link className="order-link" to={`${base}/orders/${o.id}`}>
                      {o.number}
                    </Link>
                  </td>
                  <td>
                    <b>{customerLabel(o.customer)}</b>
                  </td>
                  <td>{o.date}</td>
                  <td>{money(o.amount)}</td>
                  <td>
                    <Status>{o.status}</Status>
                  </td>
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

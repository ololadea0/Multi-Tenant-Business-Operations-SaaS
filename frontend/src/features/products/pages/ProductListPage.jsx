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

export function Products() {
  const { products } = useOrganizationData();
  const [searchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get("search") || "");
  const [filter, setFilter] = useState("All");
  const { organizationId = "northstar" } = useParams();
  const navigate = useNavigate();
  const base = `/app/${organizationId}`;
  const rows = products.filter(
    (p) =>
      (filter === "All" || p.status === filter) &&
      p.name.toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <>
      <PageHeader
        eyebrow="CATALOGUE"
        title="Products"
        description="Manage the product information your orders and inventory rely on."
        action={
          <Link className="app-btn primary" to={`${base}/products/new`}>
            <Icon name="plus" />
            Add product
          </Link>
        }
      />
      <div className="record-surface">
        <Toolbar
          search={search}
          setSearch={setSearch}
          placeholder="Search products or SKU"
        >
          <div className="filter-tabs">
            {["All", "Active", "Inactive"].map((x) => (
              <button
                className={filter === x ? "active" : ""}
                onClick={() => setFilter(x)}
                key={x}
              >
                {x}
              </button>
            ))}
          </div>
        </Toolbar>
        {rows.length ? (
          <>
            <div className="app-table-wrap">
              <table className="app-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>SKU</th>
                    <th>Selling price</th>
                    <th>Cost price</th>
                    <th>Current stock</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((p) => (
                    <tr
                      key={p.id}
                      role="link"
                      tabIndex={0}
                      onClick={(event) => {
                        if (
                          event.target.closest("a,button,input,select,textarea")
                        )
                          return;
                        navigate(`${base}/products/${p.id}`);
                      }}
                      onKeyDown={(event) => {
                        if (
                          (event.key === "Enter" || event.key === " ") &&
                          !event.target.closest(
                            "a,button,input,select,textarea",
                          )
                        ) {
                          event.preventDefault();
                          navigate(`${base}/products/${p.id}`);
                        }
                      }}
                    >
                      <td>
                        <Link
                          className="primary-cell"
                          to={`${base}/products/${p.id}`}
                        >
                          <i>{p.name[0]}</i>
                          <span>
                            <b>{p.name}</b>
                            <small>Updated 2 days ago</small>
                          </span>
                        </Link>
                      </td>
                      <td className="mono-cell">{p.sku}</td>
                      <td>{money(p.price)}</td>
                      <td>{money(p.cost)}</td>
                      <td>
                        <span
                          className={p.stock <= p.threshold ? "stock-low" : ""}
                        >
                          {p.stock}{" "}
                          {p.stock <= p.threshold && <small>Low</small>}
                        </span>
                      </td>
                      <td>
                        <Status>{p.status}</Status>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination />
          </>
        ) : (
          <EmptyState
            title="No products found"
            copy="Try changing your search or filter."
            action="Add product"
            to={`${base}/products/new`}
          />
        )}
      </div>
    </>
  );
}

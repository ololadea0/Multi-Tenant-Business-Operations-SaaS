import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router";
import { money } from "../store/format";
import { useOrganizationData } from "../store/dataHooks";
import {
  EmptyState,
  Icon,
  Notice,
  PageHeader,
  Pagination,
  Search,
  Status,
} from "./Ui";
import {
  useCreateCustomerMutation,
  useCreateInventoryMovementMutation,
  useCreateOrderMutation,
  useCreateProductMutation,
  useUpdateProductMutation,
  useCompleteOrderMutation,
  useCancelOrderMutation,
  useOrganizationQuery,
} from "../store/api";

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
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {rows.map((p) => (
                    <tr key={p.id}>
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
                      <td>
                        <Link
                          className="row-menu"
                          to={`${base}/products/${p.id}`}
                          aria-label={`Open actions for ${p.name}`}
                          title="Open product actions"
                        >
                          <Icon name="menu" />
                        </Link>
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

export function ProductForm() {
  const { products } = useOrganizationData();
  const { organizationId, productId } = useParams();
  const navigate = useNavigate();
  const [createProduct, createState] = useCreateProductMutation();
  const [updateProduct, updateState] = useUpdateProductMutation();
  const product = products.find(
    (item) => String(item.id) === String(productId),
  );
  const isEditing = Boolean(productId);
  const saveState = isEditing ? updateState : createState;
  async function submit(e) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      const payload = {
        name: form.get("name"),
        sku: form.get("sku"),
        description: form.get("description") || null,
        cost_price: form.get("cost_price") || null,
        unit_price: form.get("unit_price"),
        low_stock_threshold: Number(form.get("low_stock_threshold") || 10),
      };
      if (isEditing)
        await updateProduct({ organizationId, productId, ...payload }).unwrap();
      else
        await createProduct({
          organizationId,
          ...payload,
          stock_quantity: Number(form.get("stock_quantity") || 0),
        }).unwrap();
      navigate(`/app/${organizationId}/products`);
    } catch {}
  }
  return (
    <>
      <PageHeader
        eyebrow={isEditing ? "PRODUCTS / EDIT" : "PRODUCTS / NEW"}
        title={isEditing ? "Edit product" : "Add a product"}
        description="Create the product record first. You can update its stock at any time."
      />
      <form
        key={product?.id || "new-product"}
        className="app-form-layout"
        onSubmit={submit}
      >
        <div className="form-main">
          <FormSection
            title="Basic information"
            copy="The details your team will use to identify this product."
          >
            <label>
              Product name <em>Required</em>
              <input
                name="name"
                required
                defaultValue={product?.name || ""}
                placeholder="e.g. Field Notes — Kraft"
              />
            </label>
            <label>
              SKU <em>Required</em>
              <input
                name="sku"
                required
                defaultValue={product?.sku || ""}
                placeholder="e.g. FN-KR-01"
              />
              <small>Use a unique internal reference.</small>
            </label>
            <label>
              Description <em>Optional</em>
              <textarea
                name="description"
                rows={4}
                defaultValue={product?.description || ""}
                placeholder="Add useful product details"
              />
            </label>
          </FormSection>
          <FormSection
            title="Pricing"
            copy="Set the current selling and cost prices."
          >
            <div className="field-row">
              <label>
                Selling price <em>Required</em>
                <div className="money-input">
                  <span>₦</span>
                  <input
                    name="unit_price"
                    required
                    type="number"
                    min="0"
                    step=".01"
                    defaultValue={product?.price ?? ""}
                    placeholder="0.00"
                  />
                </div>
              </label>
              <label>
                Cost price <em>Optional</em>
                <div className="money-input">
                  <span>₦</span>
                  <input
                    name="cost_price"
                    type="number"
                    min="0"
                    step=".01"
                    defaultValue={product?.cost ?? ""}
                    placeholder="0.00"
                  />
                </div>
              </label>
            </div>
          </FormSection>
          <FormSection
            title="Starting inventory"
            copy="Add the opening stock position and when you want a low-stock warning."
          >
            <div className="field-row">
              <label>
                Initial stock
                <input
                  name="stock_quantity"
                  type="number"
                  min="0"
                  defaultValue={product?.stock ?? 0}
                  disabled={isEditing}
                />
              </label>
              <label>
                Low-stock threshold
                <input
                  name="low_stock_threshold"
                  type="number"
                  min="0"
                  defaultValue={product?.threshold ?? 10}
                />
              </label>
            </div>
          </FormSection>
        </div>
        <aside className="form-aside">
          {saveState.error && (
            <Notice tone="error">
              {saveState.error?.data?.detail ||
                "Product could not be saved. Please try again."}
            </Notice>
          )}
          <div className="form-actions">
            <button
              type="button"
              className="app-btn secondary"
              onClick={() => navigate(-1)}
            >
              Cancel
            </button>
            <button
              className="app-btn primary"
              disabled={saveState.isLoading || (isEditing && !product)}
            >
              {saveState.isLoading
                ? "Saving product…"
                : isEditing
                  ? "Update product"
                  : "Save product"}
            </button>
          </div>
        </aside>
      </form>
    </>
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

export function ProductDetails() {
  const { products, movements } = useOrganizationData();
  const { organizationId = "northstar", productId } = useParams();
  const p = products.find((x) => x.id === productId) || products[0];
  const base = `/app/${organizationId}`;
  return (
    <>
      <PageHeader
        eyebrow={`PRODUCTS / ${p.sku}`}
        title={p.name}
        description="Product information, pricing and current inventory position."
        action={
          <div className="head-actions">
            <button className="app-btn secondary">Deactivate</button>
            <Link
              className="app-btn primary"
              to={`${base}/products/${p.id}/edit`}
            >
              Edit product
            </Link>
          </div>
        }
      />
      <div className="detail-grid">
        <section className="detail-main">
          <div className="detail-block">
            <h2>Product information</h2>
            <dl>
              <div>
                <dt>SKU</dt>
                <dd>{p.sku}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>
                  <Status>{p.status}</Status>
                </dd>
              </div>
              <div>
                <dt>Selling price</dt>
                <dd>{money(p.price)}</dd>
              </div>
              <div>
                <dt>Cost price</dt>
                <dd>{money(p.cost)}</dd>
              </div>
            </dl>
          </div>
          <div className="detail-block">
            <div className="panel-heading">
              <div>
                <span>Inventory history</span>
                <small>Recent stock movement for this product</small>
              </div>
              <Link to={`${base}/inventory`}>View all →</Link>
            </div>
            {movements.slice(0, 3).map((m) => (
              <div className="detail-event" key={m.date}>
                <Status>{m.type}</Status>
                <span>
                  <b>{m.quantity} units</b>
                  <small>
                    {m.date} · {m.user}
                  </small>
                </span>
                <em>
                  {m.previous} → {m.current}
                </em>
              </div>
            ))}
          </div>
        </section>
        <aside className="stock-summary">
          <span>CURRENT STOCK</span>
          <strong>{p.stock}</strong>
          <p>units available</p>
          <hr />
          <div>
            <span>Low-stock threshold</span>
            <b>{p.threshold} units</b>
          </div>
          <Link className="app-btn primary" to={`${base}/inventory`}>
            Record movement
          </Link>
        </aside>
      </div>
    </>
  );
}

export function Inventory() {
  const { products, movements } = useOrganizationData();
  const [movement, setMovement] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const { organizationId } = useParams();
  const totalUnits = products.reduce(
    (sum, product) => sum + Number(product.stock || 0),
    0,
  );
  const stockValue = products.reduce(
    (sum, product) =>
      sum + Number(product.stock || 0) * Number(product.cost || 0),
    0,
  );
  const lowStockProducts = products.filter(
    (product) => product.stock <= product.threshold,
  );
  function downloadInventory(format) {
    const headers = [
      "Date",
      "Product",
      "Type",
      "Quantity",
      "Previous stock",
      "New stock",
      "Recorded by",
    ];
    const rows = movements.map((item) => [
      item.date,
      item.product,
      item.type,
      item.quantity,
      item.previous,
      item.current,
      item.user,
    ]);
    const escapeCell = (value) => String(value ?? "").replaceAll('"', '""');
    const content =
      format === "csv"
        ? [headers, ...rows]
            .map((row) =>
              row.map((value) => `"${escapeCell(value)}"`).join(","),
            )
            .join("\r\n")
        : [headers, ...rows]
            .map((row) => row.map((value) => escapeCell(value)).join("\t"))
            .join("\r\n");
    const blob = new Blob(["\ufeff", content], {
      type:
        format === "csv"
          ? "text/csv;charset=utf-8"
          : "application/vnd.ms-excel",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `daymark-inventory-${new Date().toISOString().slice(0, 10)}.${format === "csv" ? "csv" : "xls"}`;
    link.click();
    URL.revokeObjectURL(url);
    setExportOpen(false);
  }
  return (
    <>
      <PageHeader
        eyebrow="STOCK CONTROL"
        title="Inventory"
        description="Understand your stock position and record every change clearly."
        action={
          <button className="app-btn primary" onClick={() => setMovement(true)}>
            <Icon name="plus" />
            Record movement
          </button>
        }
      />
      <section className="inventory-summary">
        <div>
          <span>Total units on hand</span>
          <strong>{totalUnits.toLocaleString()}</strong>
          <small>Across {products.length} active products</small>
        </div>
        <div>
          <span>Stock value</span>
          <strong>{money(stockValue)}</strong>
          <small>Based on recorded cost price</small>
        </div>
        <div>
          <span>Needs attention</span>
          <strong>{lowStockProducts.length}</strong>
          <small>At or below reorder threshold</small>
        </div>
      </section>
      <div className="inventory-layout">
        <section className="record-surface">
          <div className="panel-heading padded">
            <div>
              <span>Movement history</span>
              <small>Every stock change in this workspace</small>
            </div>
            <div className="export-actions">
              <button type="button" onClick={() => setExportOpen(!exportOpen)}>
                Export
              </button>
              {exportOpen && (
                <div className="export-menu">
                  <button
                    type="button"
                    onClick={() => downloadInventory("csv")}
                  >
                    Download CSV
                  </button>
                  <button
                    type="button"
                    onClick={() => downloadInventory("excel")}
                  >
                    Download Excel
                  </button>
                </div>
              )}
            </div>
          </div>
          <div className="app-table-wrap">
            <table className="app-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Product</th>
                  <th>Type</th>
                  <th>Quantity</th>
                  <th>Previous</th>
                  <th>New stock</th>
                  <th>Recorded by</th>
                </tr>
              </thead>
              <tbody>
                {movements.map((m) => (
                  <tr key={m.date}>
                    <td>{m.date}</td>
                    <td>
                      <b>{m.product}</b>
                    </td>
                    <td>
                      <Status>{m.type}</Status>
                    </td>
                    <td>
                      <b className={m.type === "OUT" ? "negative" : "positive"}>
                        {m.quantity}
                      </b>
                    </td>
                    <td>{m.previous}</td>
                    <td>
                      <b>{m.current}</b>
                    </td>
                    <td>{m.user}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <aside className="low-stock-panel">
          <div className="panel-heading">
            <div>
              <span>Low stock</span>
              <small>{lowStockProducts.length} products need review</small>
            </div>
          </div>
          {products
            .filter((p) => p.stock <= p.threshold)
            .map((p) => (
              <div key={p.id}>
                <i>{p.name[0]}</i>
                <span>
                  <b>{p.name}</b>
                  <small>
                    {p.stock} left · Reorder at {p.threshold}
                  </small>
                </span>
                <Link to={`/app/${organizationId}/products/${p.id}`}>View</Link>
              </div>
            ))}
        </aside>
      </div>
      {movement && (
        <MovementDialog
          products={products}
          organizationId={organizationId}
          close={() => setMovement(false)}
        />
      )}
    </>
  );
}

function MovementDialog({ close, products, organizationId }) {
  const [type, setType] = useState("IN");
  const [productId, setProductId] = useState("");
  const [reason, setReason] = useState("");
  const [createMovement, movementState] = useCreateInventoryMovementMutation();
  async function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createMovement({
        organizationId,
        productId,
        movement_type: type.toLowerCase(),
        quantity: Number(form.get("quantity")),
        reason: type === "OUT" ? reason : undefined,
        note: form.get("note") || null,
      }).unwrap();
      close();
    } catch {}
  }
  return (
    <div className="dialog-layer">
      <button className="dialog-scrim" onClick={close} />
      <form className="app-dialog" onSubmit={submit}>
        <header>
          <div>
            <span>INVENTORY</span>
            <h2>Record stock movement</h2>
          </div>
          <button type="button" onClick={close}>
            ×
          </button>
        </header>
        <label>
          Product
          <select
            required
            value={productId}
            onChange={(event) => setProductId(event.target.value)}
          >
            <option value="">Select a product</option>
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name} ({product.stock} in stock)
              </option>
            ))}
          </select>
        </label>
        <fieldset>
          <legend>Movement type</legend>
          <div className="movement-types">
            {[
              ["IN", "Stock received"],
              ["OUT", "Stock removed"],
              ["ADJUSTMENT", "Stock corrected"],
            ].map((x) => (
              <button
                className={type === x[0] ? "active" : ""}
                type="button"
                onClick={() => {
                  setType(x[0]);
                  if (x[0] !== "OUT") setReason("");
                }}
                key={x[0]}
              >
                <b>{x[0]}</b>
                <small>{x[1]}</small>
              </button>
            ))}
          </div>
        </fieldset>
        <label>
          Quantity
          <input required name="quantity" type="number" min="1" />
        </label>
        {type === "OUT" && (
          <label>
            Reason <em>Required</em>
            <select
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              required
            >
              <option value="">Select a reason</option>
              <option value="sale">Sale</option>
              <option value="damage">Damage</option>
              <option value="expired">Expired</option>
              <option value="loss">Loss</option>
              <option value="sample">Sample</option>
              <option value="transfer">Transfer</option>
              <option value="return">Return</option>
              <option value="other">Other</option>
            </select>
          </label>
        )}
        <label>
          Reason or note <em>Optional</em>
          <textarea
            name="note"
            rows={3}
            placeholder="Add context for this movement"
          />
        </label>
        <div className="stock-result">
          <span>
            Current stock{" "}
            <b>
              {products.find((product) => product.id === productId)?.stock || 0}
            </b>
          </span>
          <i>→</i>
          <span>
            Resulting stock{" "}
            <b>
              {productId
                ? Number(
                    products.find(
                      (product) => String(product.id) === String(productId),
                    )?.stock || 0,
                  ) + (type === "OUT" ? -1 : 1)
                : "—"}
            </b>
          </span>
        </div>
        <footer>
          <button type="button" className="app-btn secondary" onClick={close}>
            Cancel
          </button>
          <button
            className="app-btn primary"
            disabled={
              movementState.isLoading ||
              !productId ||
              (type === "OUT" && !reason)
            }
          >
            {movementState.isLoading ? "Recording…" : "Record movement"}
          </button>
          {movementState.error && (
            <Notice tone="error">
              {movementState.error?.data?.detail ||
                "The inventory movement could not be recorded."}
            </Notice>
          )}
        </footer>
      </form>
    </div>
  );
}

export function Customers() {
  const { customers } = useOrganizationData();
  const [search, setSearch] = useState("");
  const { organizationId = "northstar" } = useParams();
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
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id}>
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
                  <td>{c.added}</td>
                  <td>
                    <Link
                      className="row-menu"
                      to={`${base}/customers/${c.id}`}
                      aria-label={`Open actions for ${c.name}`}
                      title="Open customer actions"
                    >
                      <Icon name="menu" />
                    </Link>
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

export function CustomerForm() {
  const { customers } = useOrganizationData();
  return (
    <SimpleRecordForm
      title="Add a customer"
      eyebrow="CUSTOMERS / NEW"
      description="Create a customer record for orders and contact history"
      fields={["Customer name", "Email address", "Phone number"]}
    />
  );
}

function SimpleRecordForm({ title, eyebrow, description, fields }) {
  const nav = useNavigate();
  const { organizationId } = useParams();
  const [createCustomer, customerState] = useCreateCustomerMutation();
  async function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createCustomer({
        organizationId,
        name: form.get("name"),
        email: form.get("email") || null,
        phone: form.get("phone") || null,
      }).unwrap();
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
          <button
            className="app-btn primary"
            disabled={customerState.isLoading}
          >
            {customerState.isLoading ? "Saving…" : "Save customer"}
          </button>
          {customerState.error && (
            <Notice tone="error">
              {customerState.error?.data?.detail ||
                "Customer could not be saved."}
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
  const c = customers.find((x) => x.id === customerId) || customers[0];
  const base = `/app/${organizationId}`;
  return (
    <>
      <PageHeader
        eyebrow="CUSTOMER RECORD"
        title={c.name}
        description={`Customer since ${c.added}`}
        action={<button className="app-btn primary">Edit customer</button>}
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

export function Orders() {
  const { orders } = useOrganizationData();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const { organizationId = "northstar" } = useParams();
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
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((o) => (
                <tr key={o.id}>
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
                  <td>
                    <Link
                      className="row-menu"
                      to={`${base}/orders/${o.id}`}
                      aria-label={`Open actions for ${o.number}`}
                      title="Open order actions"
                    >
                      <Icon name="menu" />
                    </Link>
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

export function CreateOrder() {
  const { products, customers } = useOrganizationData();
  const [lines, setLines] = useState([]);
  useEffect(() => {
    if (!lines.length && products.length)
      setLines(
        products
          .slice(0, 2)
          .map((product, index) => ({ product, qty: index === 0 ? 2 : 1 })),
      );
  }, [products, lines.length]);
  const { organizationId = "northstar" } = useParams();
  const nav = useNavigate();
  const [customerId, setCustomerId] = useState("");
  const [createOrder, orderState] = useCreateOrderMutation();
  useEffect(() => {
    if (!customerId && customers.length) setCustomerId(String(customers[0].id));
  }, [customers, customerId]);
  async function submitOrder() {
    try {
      await createOrder({
        organizationId,
        customer_id: Number(customerId),
        items: lines
          .filter((line) => line.product)
          .map((line) => ({
            product_id: line.product.id,
            quantity: Number(line.qty),
          })),
      }).unwrap();
      nav(`/app/${organizationId}/orders`);
    } catch {}
  }
  const subtotal = useMemo(
    () =>
      lines.reduce(
        (a, l) => a + Number(l.product?.price || 0) * Number(l.qty || 0),
        0,
      ),
    [lines],
  );
  return (
    <>
      <PageHeader
        eyebrow="ORDERS / NEW"
        title="Create an order"
        description="Add a customer and the products they are ordering."
      />
      <div className="order-builder">
        <section>
          <div className="builder-section">
            <header>
              <span>01</span>
              <div>
                <h2>Customer</h2>
                <p>Who is this order for?</p>
              </div>
            </header>
            <select
              value={customerId}
              onChange={(event) => setCustomerId(event.target.value)}
              required
            >
              <option value="">Select a customer</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div className="builder-section">
            <header>
              <span>02</span>
              <div>
                <h2>Order items</h2>
                <p>Add products and confirm quantities.</p>
              </div>
            </header>
            <div className="line-head">
              <span>Product</span>
              <span>Price</span>
              <span>Qty</span>
              <span>Total</span>
              <span />
            </div>
            {lines.map(
              (l, i) =>
                l.product && (
                  <div className="order-line" key={l.product.id || i}>
                    <select
                      value={l.product.id}
                      onChange={(event) => {
                        const selected = products.find(
                          (product) =>
                            String(product.id) === event.target.value,
                        );
                        if (selected)
                          setLines(
                            lines.map((line, index) =>
                              index === i
                                ? { ...line, product: selected }
                                : line,
                            ),
                          );
                      }}
                    >
                      <option value={l.product.id}>{l.product.name}</option>
                      {products
                        .filter((p) => p.id !== l.product.id)
                        .map((p) => (
                          <option value={p.id} key={p.id}>
                            {p.name}
                          </option>
                        ))}
                    </select>
                    <span>{money(l.product.price)}</span>
                    <input
                      type="number"
                      min="1"
                      value={l.qty}
                      onChange={(e) =>
                        setLines(
                          lines.map((x, j) =>
                            j === i ? { ...x, qty: Number(e.target.value) } : x,
                          ),
                        )
                      }
                    />
                    <b>
                      {money(Number(l.product.price || 0) * Number(l.qty || 0))}
                    </b>
                    <button
                      onClick={() => setLines(lines.filter((_, j) => j !== i))}
                    >
                      ×
                    </button>
                  </div>
                ),
            )}
            <button
              className="add-line"
              onClick={() =>
                products.length &&
                setLines([
                  ...lines,
                  {
                    product:
                      products.find(
                        (product) =>
                          !lines.some(
                            (line) => line.product?.id === product.id,
                          ),
                      ) || products[0],
                    qty: 1,
                  },
                ])
              }
            >
              + Add another product
            </button>
          </div>
          <div className="builder-section">
            <header>
              <span>03</span>
              <div>
                <h2>Order note</h2>
                <p>Optional context for your team.</p>
              </div>
            </header>
            <textarea rows={3} placeholder="Add delivery or handling notes" />
          </div>
        </section>
        <aside className="order-summary">
          <span>ORDER SUMMARY</span>
          <h3>
            {customers.find((customer) => String(customer.id) === customerId)
              ?.name || "Select a customer"}
          </h3>
          <div>
            {lines
              .filter((line) => line.product)
              .map((l, i) => (
                <p key={i}>
                  <span>
                    {l.qty} × {l.product.name}
                  </span>
                  <b>
                    {money(Number(l.qty || 0) * Number(l.product?.price || 0))}
                  </b>
                </p>
              ))}
          </div>
          <hr />
          <p>
            <span>Subtotal</span>
            <b>{money(subtotal)}</b>
          </p>
          <p className="total">
            <span>Order total</span>
            <b>{money(subtotal)}</b>
          </p>
          <Notice tone="warning">
            Creating this order will reduce available inventory.
          </Notice>
          <button
            className="app-btn primary"
            onClick={submitOrder}
            disabled={orderState.isLoading || !customerId || !lines.length}
          >
            {orderState.isLoading ? "Creating…" : "Create order"}
          </button>
          {orderState.error && (
            <Notice tone="error">
              {orderState.error?.data?.detail ||
                "The order could not be created."}
            </Notice>
          )}
          <button className="app-btn secondary" onClick={() => nav(-1)}>
            Save locally as draft
          </button>
        </aside>
      </div>
    </>
  );
}

export function OrderDetails() {
  const { orders, products, customers, organizationId } = useOrganizationData();
  const { data: organization } = useOrganizationQuery(organizationId, {
    skip: !organizationId,
  });
  const { orderId } = useParams();
  const [completeOrder, completeState] = useCompleteOrderMutation();
  const [cancelOrder, cancelState] = useCancelOrderMutation();
  const [confirm, setConfirm] = useState(false);

  const o = useMemo(
    () => orders.find((x) => String(x.id) === String(orderId)) || orders[0],
    [orders, orderId],
  );

  const customer = customers.find(
    (item) => String(item.id) === String(o?.customer),
  );
  const status = String(o?.status || "").toLowerCase();
  const customerName =
    customer?.name || customer?.email || `Customer #${o?.customer ?? "—"}`;
  const customerEmail = customer?.email || "No email on file";
  const organizationName = organization?.name || "Organization";
  const organizationAddress = [
    organization?.address_line_1,
    organization?.address_line_2,
    [organization?.city, organization?.state, organization?.postal_code]
      .filter(Boolean)
      .join(", "),
    organization?.country,
  ]
    .filter(Boolean)
    .join("\n");
  const organizationContact = [organization?.email, organization?.phone]
    .filter(Boolean)
    .join(" • ");

  async function complete() {
    try {
      await completeOrder({ organizationId, orderId }).unwrap();
    } catch {}
  }

  async function cancel() {
    try {
      await cancelOrder({ organizationId, orderId }).unwrap();
      setConfirm(false);
    } catch {}
  }

  function openReceipt() {
    if (!o) return;

    const escapeHtml = (value) =>
      String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#039;");

    const orderLines = (o.items || [])
      .map((item) => {
        const product = products.find(
          (entry) => String(entry.id) === String(item.product_id),
        );
        const productName = product?.name || `Product #${item.product_id}`;
        const productDetails = product?.description?.trim();
        const unitPrice = Number(item.unit_price || product?.price || 0);
        const total = unitPrice * Number(item.quantity || 0);
        const detailsHtml = productDetails
          ? `<div class="item-details">${escapeHtml(productDetails)}</div>`
          : "";

        return `
          <tr>
            <td>
              <div class="item-name">${escapeHtml(productName)}</div>
              ${detailsHtml}
            </td>
            <td>${item.quantity}</td>
            <td>${money(unitPrice)}</td>
            <td>${money(total)}</td>
          </tr>
        `;
      })
      .join("");
    const formattedOrgAddress = organizationAddress
      ? organizationAddress
          .split("\n")
          .map((line) => `<div>${escapeHtml(line)}</div>`)
          .join("")
      : "";
    const organizationMeta = organizationContact
      ? `<div class="org-contact">${escapeHtml(organizationContact)}</div>`
      : "";

    const receipt = window.open("", "_blank", "width=900,height=800");
    if (!receipt) return;

    const dateLabel = new Date(o.created_at || Date.now()).toLocaleString();
    const html = `<!doctype html>
      <html>
        <head>
          <meta charset="utf-8" />
          <title>Receipt - ${o.number}</title>
          <style>
            @page { size: A4; margin: 18mm; }
            :root {
              --ink: #111827;
              --muted: #5f6d68;
              --line: #dfe7e2;
              --panel: #f5f7f5;
              --accent: #17211e;
              --accent-soft: #edf4ee;
              --highlight: #e8f4ea;
            }
            * { box-sizing: border-box; }
            body {
              margin: 0;
              background: #f0f2ef;
              font-family: Arial, Helvetica, sans-serif;
              color: var(--ink);
              padding: 24px;
            }
            .receipt {
              max-width: 760px;
              margin: 0 auto;
              background: linear-gradient(180deg, #ffffff 0%, #fbfcfb 100%);
              border: 1px solid var(--line);
              border-radius: 22px;
              box-shadow: 0 24px 60px rgba(23, 33, 30, 0.08);
              padding: 32px;
            }
            .header {
              display: flex;
              justify-content: space-between;
              align-items: flex-start;
              gap: 24px;
              border-bottom: 1px solid var(--line);
              padding-bottom: 22px;
              margin-bottom: 22px;
            }
            .brand {
              display: flex;
              align-items: center;
              gap: 12px;
            }
            .brand-mark {
              width: 42px;
              height: 42px;
              border-radius: 14px;
              background: linear-gradient(135deg, var(--accent), #2a3f3b);
              color: white;
              display: grid;
              place-items: center;
              font-weight: 700;
              font-size: 15px;
            }
            .eyebrow {
              display: inline-block;
              letter-spacing: 0.12em;
              text-transform: uppercase;
              font-size: 10px;
              color: var(--muted);
              margin-bottom: 8px;
            }
            h1 {
              margin: 0;
              font-size: 30px;
              line-height: 1.15;
            }
            .order-box {
              min-width: 190px;
              background: linear-gradient(135deg, var(--panel), var(--accent-soft));
              border: 1px solid var(--line);
              border-radius: 14px;
              padding: 14px 18px;
              text-align: right;
            }
            .order-box span {
              display: block;
              color: var(--muted);
              font-size: 10px;
              letter-spacing: 0.08em;
              text-transform: uppercase;
              margin-bottom: 6px;
            }
            .order-box strong {
              font-size: 24px;
            }
            .customer-card {
              display: flex;
              justify-content: space-between;
              gap: 16px;
              background: var(--panel);
              border: 1px solid var(--line);
              border-radius: 14px;
              padding: 16px 18px;
              margin-bottom: 22px;
            }
            .org-brand {
              display: flex;
              flex-direction: column;
              align-items: flex-end;
              text-align: right;
              gap: 6px;
              min-width: 180px;
            }
            .org-brand .small-mark {
              width: 28px;
              height: 28px;
              display: grid;
              place-items: center;
              border-radius: 8px;
              background: linear-gradient(135deg, var(--accent), #2a3f3b);
              color: #fff;
              font-size: 12px;
              font-weight: 700;
            }
            .org-brand .org-address,
            .org-contact {
              color: var(--muted);
              font-size: 11px;
              line-height: 1.5;
            }
            .customer-card h2 {
              margin: 0 0 6px;
              font-size: 15px;
            }
            .customer-card p {
              margin: 0;
              font-size: 13px;
              color: var(--muted);
              line-height: 1.6;
            }
            .status-pill {
              align-self: center;
              background: var(--highlight);
              color: #244e31;
              border: 1px solid #cfe7d4;
              padding: 8px 12px;
              border-radius: 999px;
              font-size: 11px;
              font-weight: 700;
              letter-spacing: 0.08em;
              text-transform: uppercase;
            }
            .meta {
              display: grid;
              grid-template-columns: repeat(3, minmax(0, 1fr));
              gap: 16px;
              margin-bottom: 24px;
            }
            .meta-box {
              background: var(--panel);
              border: 1px solid var(--line);
              border-radius: 12px;
              padding: 12px 14px;
            }
            .meta-box label {
              display: block;
              font-size: 10px;
              color: var(--muted);
              letter-spacing: 0.08em;
              text-transform: uppercase;
              margin-bottom: 6px;
            }
            .meta-box strong {
              font-size: 14px;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin-top: 6px;
            }
            th, td {
              border-bottom: 1px solid var(--line);
              padding: 12px 8px;
              text-align: left;
            }
            th {
              color: var(--muted);
              text-transform: uppercase;
              letter-spacing: 0.08em;
              font-size: 10px;
            }
            td {
              font-size: 13px;
            }
            .item-name {
              font-weight: 600;
            }
            .item-details {
              margin-top: 4px;
              color: var(--muted);
              font-size: 11px;
              line-height: 1.45;
            }
            .summary {
              display: flex;
              justify-content: flex-end;
              margin-top: 18px;
            }
            .summary-box {
              min-width: 260px;
              border: 1px solid var(--line);
              border-radius: 12px;
              padding: 16px;
              background: #fbfcfb;
            }
            .summary-row {
              display: flex;
              justify-content: space-between;
              font-size: 13px;
              margin-bottom: 10px;
            }
            .summary-row.total {
              border-top: 1px solid var(--line);
              padding-top: 12px;
              margin-top: 10px;
              font-size: 18px;
              font-weight: 700;
            }
            .thankyou {
              margin-top: 26px;
              padding-top: 18px;
              border-top: 1px solid var(--line);
              text-align: center;
              color: var(--muted);
              font-size: 13px;
              line-height: 1.7;
            }
            .thankyou strong {
              color: var(--ink);
            }
            @media print {
              body { background: white; padding: 0; }
              .receipt { box-shadow: none; border: none; border-radius: 0; }
            }
          </style>
        </head>
        <body>
          <div class="receipt">
            <div class="header">
              <div class="brand">
                <div class="brand-mark">D</div>
                <div>
                  <div class="eyebrow">Receipt</div>
                  <h1>${organizationName}</h1>
                </div>
              </div>
              <div class="order-box">
                <span>Order</span>
                <strong>${o.number}</strong>
              </div>
            </div>
            <div class="customer-card">
              <div>
                <h2>Bill to</h2>
                <p><strong>${customerName}</strong><br />${customerEmail}</p>
              </div>
              <div class="org-brand">
                <div class="small-mark">D</div>
                <div class="org-address">${formattedOrgAddress || "<div>Business address</div>"}</div>
                ${organizationMeta}
              </div>
              <div class="status-pill">${String(o.status || "completed").toUpperCase()}</div>
            </div>
            <div class="meta">
              <div class="meta-box">
                <label>Customer</label>
                <strong>${customerName}</strong>
              </div>
              <div class="meta-box">
                <label>Email</label>
                <strong>${customerEmail}</strong>
              </div>
              <div class="meta-box">
                <label>Date</label>
                <strong>${dateLabel}</strong>
              </div>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Qty</th>
                  <th>Unit price</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>${orderLines || "<tr><td colspan='4'>No items recorded</td></tr>"}</tbody>
            </table>
            <div class="summary">
              <div class="summary-box">
                <div class="summary-row"><span>Subtotal</span><span>${money(o.amount)}</span></div>
                <div class="summary-row total"><span>Total</span><span>${money(o.amount)}</span></div>
              </div>
            </div>
            <div class="thankyou">
              <strong>Thank you for your order.</strong><br />
              We appreciate your business and look forward to serving you again.
            </div>
          </div>
          <script>
            window.onload = function () {
              setTimeout(function () {
                window.print();
              }, 200);
            };
          </script>
        </body>
      </html>
    `;

    receipt.document.write(html);
    receipt.document.close();
    receipt.focus();
  }

  if (!o)
    return (
      <EmptyState
        title="Order not found"
        copy="This order is not available in the current organization."
        to="../orders"
      />
    );

  return (
    <>
      <PageHeader
        eyebrow={`ORDERS / ${o.number}`}
        title={`Order ${o.number}`}
        description={`Created ${o.date} · ${customerName}`}
        action={
          <div className="head-actions">
            {status === "completed" && (
              <button className="app-btn secondary" onClick={openReceipt}>
                Download receipt
              </button>
            )}
            {status !== "completed" && status !== "cancelled" && (
              <button
                className="app-btn secondary danger"
                onClick={() => setConfirm(true)}
                disabled={status === "cancelled"}
              >
                Cancel order
              </button>
            )}
            <button
              className="app-btn primary"
              onClick={complete}
              disabled={completeState.isLoading || status !== "confirmed"}
            >
              {completeState.isLoading ? "Completing…" : "Complete order"}
            </button>
          </div>
        }
      />
      <div className="order-detail-layout">
        <section>
          <div className="detail-block order-items">
            <div className="panel-heading">
              <div>
                <span>Order items</span>
                <small>{o.items?.length || 0} line items</small>
              </div>
              <Status>{o.status}</Status>
            </div>
            <div className="item-head">
              <span>Product</span>
              <span>Unit price</span>
              <span>Qty</span>
              <span>Total</span>
            </div>
            {(o.items || []).map((item) => {
              const product = products.find(
                (entry) => String(entry.id) === String(item.product_id),
              );
              const unitPrice = Number(item.unit_price || product?.price || 0);
              return (
                <div className="item-row" key={item.id || item.product_id}>
                  <span>
                    <i>{product?.name?.[0] || "?"}</i>
                    <b>{product?.name || `Product #${item.product_id}`}</b>
                  </span>
                  <span>{money(unitPrice)}</span>
                  <span>{item.quantity}</span>
                  <b>{money(unitPrice * Number(item.quantity || 0))}</b>
                </div>
              );
            })}
            <div className="order-total">
              <span>Order total</span>
              <strong>{money(o.amount)}</strong>
            </div>
          </div>
          <div className="detail-block">
            <h2>Order timeline</h2>
            <div className="timeline">
              <div className="done">
                <i />
                <span>
                  <b>Order created</b>
                  <small>
                    {o.created_at
                      ? new Date(o.created_at).toLocaleString()
                      : "—"}
                  </small>
                </span>
              </div>
              <div className="done">
                <i />
                <span>
                  <b>Order confirmed</b>
                  <small>
                    {o.updated_at
                      ? new Date(o.updated_at).toLocaleString()
                      : "—"}
                  </small>
                </span>
              </div>
              <div>
                <i />
                <span>
                  <b>Order completed</b>
                  <small>Waiting for completion</small>
                </span>
              </div>
            </div>
          </div>
        </section>
        <aside className="order-customer">
          <span>CUSTOMER</span>
          <h3>{o.customer}</h3>
          <p>
            {customer?.email || "No email available"}
            <br />
            {customer?.phone || "No phone available"}
          </p>
          <hr />
          <span>INVENTORY EFFECT</span>
          <p>
            Stock was reserved when this order was created. Cancellation
            restores stock according to the configured backend workflow.
          </p>
        </aside>
      </div>
      {confirm && (
        <ConfirmDialog
          close={() => setConfirm(false)}
          onConfirm={cancel}
          submitting={cancelState.isLoading}
        />
      )}
    </>
  );
}

function ConfirmDialog({ close, onConfirm, submitting }) {
  return (
    <div className="dialog-layer">
      <button className="dialog-scrim" onClick={close} />
      <div className="confirm-dialog">
        <div className="warning-icon">
          <Icon name="alert" />
        </div>
        <h2>Cancel this order?</h2>
        <p>
          This action changes the order status and may restore reserved stock.
          This cannot be undone.
        </p>
        <div>
          <button className="app-btn secondary" onClick={close}>
            Keep order
          </button>
          <button
            className="app-btn danger-fill"
            onClick={onConfirm}
            disabled={submitting}
          >
            {submitting ? "Cancelling…" : "Cancel order"}
          </button>
        </div>
      </div>
    </div>
  );
}

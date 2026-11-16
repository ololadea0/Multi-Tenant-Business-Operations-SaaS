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


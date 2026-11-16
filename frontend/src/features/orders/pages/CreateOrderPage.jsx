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


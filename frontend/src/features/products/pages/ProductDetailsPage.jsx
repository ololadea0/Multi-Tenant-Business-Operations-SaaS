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

export function ProductDetails() {
  const { products, movements } = useOrganizationData();
  const { organizationId = "northstar", productId } = useParams();
  const product =
    products.find((x) => String(x.id) === String(productId)) ??
    products[0] ??
    null;
  const base = `/app/${organizationId}`;

  if (!product) {
    return (
      <EmptyState
        title="Product not found"
        copy="This product is not available in the current workspace."
        to={`${base}/products`}
      />
    );
  }

  return (
    <>
      <PageHeader
        eyebrow={`PRODUCTS / ${product.sku || "—"}`}
        title={product.name}
        description="Product information, pricing and current inventory position."
        action={
          <div className="head-actions">
            <button className="app-btn secondary">Deactivate</button>
            <Link
              className="app-btn primary"
              to={`${base}/products/${product.id}/edit`}
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
                <dd>{product.sku || "—"}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>
                  <Status>{product.status || "Active"}</Status>
                </dd>
              </div>
              <div>
                <dt>Selling price</dt>
                <dd>{money(product.price ?? 0)}</dd>
              </div>
              <div>
                <dt>Cost price</dt>
                <dd>{money(product.cost ?? 0)}</dd>
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
            {(movements || []).slice(0, 3).map((m) => (
              <div className="detail-event" key={`${m.date}-${m.type}`}>
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
          <strong>{product.stock ?? 0}</strong>
          <p>units available</p>
          <hr />
          <div>
            <span>Low-stock threshold</span>
            <b>{product.threshold ?? 0} units</b>
          </div>
          <Link className="app-btn primary" to={`${base}/inventory`}>
            Record movement
          </Link>
        </aside>
      </div>
    </>
  );
}

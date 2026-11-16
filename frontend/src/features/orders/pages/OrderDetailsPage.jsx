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

const WAT_TIME_ZONE = "Africa/Lagos";

function formatWatDate(value, options = {}) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-NG", {
    timeZone: WAT_TIME_ZONE,
    ...options,
  }).format(date);
}

function normalizeWhatsappNumber(value) {
  if (!value) return null;

  const digits = String(value).replace(/\D/g, "");
  if (!digits) return null;

  if (digits.startsWith("234") && digits.length >= 11) return digits;
  if (digits.startsWith("0") && digits.length === 11)
    return `234${digits.slice(1)}`;
  if (digits.length === 10) return `234${digits}`;
  if (digits.length > 10) return digits.replace(/^00/, "");

  return null;
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

  function shareReceipt(mode = "share") {
    if (!o) return;

    const total = money(o.amount || 0);
    const translatedOrderDate = formatWatDate(o.created_at || Date.now(), {
      dateStyle: "medium",
      timeStyle: "short",
    });
    const shareText = [
      `Receipt ${o.number}`,
      `Customer: ${customerName}`,
      `Email: ${customerEmail}`,
      `Amount: ${total}`,
      `Order date: ${translatedOrderDate}`,
      `Organization: ${organizationName}`,
    ].join("\n");

    const subject = encodeURIComponent(
      `Receipt ${o.number} - ${organizationName}`,
    );
    const body = encodeURIComponent(
      `${shareText}\n\nView the order in Daymark.`,
    );

    if (mode === "email") {
      window.location.href = `mailto:?subject=${subject}&body=${body}`;
      return;
    }

    if (mode === "pdf") {
      const printWindow = window.open("", "_blank", "noopener,noreferrer");
      if (!printWindow) {
        window.alert(
          "Your browser blocked the PDF export dialog. Please allow popups and try again.",
        );
        return;
      }

      const html = `
        <html>
          <head><title>Receipt ${o.number}</title></head>
          <body style="font-family:Arial,sans-serif;padding:32px;color:#111827;line-height:1.6;">
            <h2 style="margin-bottom:8px;">Receipt ${o.number}</h2>
            <p><strong>Customer:</strong> ${customerName}</p>
            <p><strong>Email:</strong> ${customerEmail}</p>
            <p><strong>Organization:</strong> ${organizationName}</p>
            <p><strong>Order date:</strong> ${translatedOrderDate}</p>
            <p><strong>Amount:</strong> ${total}</p>
            <div style="margin-top:20px;border-top:1px solid #d1d5db;padding-top:16px;">
              <p>Thank you for shopping with Daymark.</p>
            </div>
          </body>
        </html>
      `;
      printWindow.document.write(html);
      printWindow.document.close();
      setTimeout(() => printWindow.focus(), 150);
      setTimeout(() => printWindow.print(), 300);
      return;
    }

    if (mode === "whatsapp") {
      const waNumber = normalizeWhatsappNumber(customer?.phone);
      const whatsappUrl = waNumber
        ? `https://wa.me/${waNumber}?text=${encodeURIComponent(shareText)}`
        : `https://wa.me/?text=${encodeURIComponent(shareText)}`;
      window.open(whatsappUrl, "_blank", "noopener,noreferrer");
      return;
    }

    if (navigator.share) {
      navigator
        .share({
          title: `Receipt ${o.number}`,
          text: shareText,
          url: window.location.href,
        })
        .catch(() => undefined);
      return;
    }

    navigator.clipboard?.writeText(shareText).catch(() => undefined);
    window.alert("Receipt details copied to your clipboard.");
  }

  const receiptActions = [
    { key: "share", label: "Share" },
    { key: "pdf", label: "Download PDF" },
    { key: "whatsapp", label: "WhatsApp" },
    { key: "email", label: "Email" },
  ];

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
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {receiptActions.map((entry) => (
                  <button
                    key={entry.key}
                    className="app-btn secondary"
                    onClick={() => shareReceipt(entry.key)}
                  >
                    {entry.label}
                  </button>
                ))}
              </div>
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
                      ? formatWatDate(o.created_at, {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })
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
                      ? formatWatDate(o.updated_at, {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })
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

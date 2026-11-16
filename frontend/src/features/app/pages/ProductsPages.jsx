import { useState } from "react";
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
  useCreateProductMutation,
  useUpdateProductMutation,
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

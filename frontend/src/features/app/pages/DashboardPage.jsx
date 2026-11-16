import { Link, useParams } from "react-router";
import { useMeQuery, useOrganizationQuery } from "../../../app/store/api";
import { money } from "../../../app/store/format";
import { useOrganizationData } from "../../../app/store/dataHooks";
import { Icon, PageHeader, Status } from "../../../app/application/Ui";

export function Dashboard() {
  const { organizationId } = useParams();
  const { activities, orders, products, dashboard } = useOrganizationData();
  const { data: user } = useMeQuery();
  const { data: organization } = useOrganizationQuery(organizationId, {
    skip: !organizationId,
  });
  const overview = dashboard?.overview || {};
  const today = dashboard?.today || {};
  const thisWeek = dashboard?.this_week || {};
  const thisMonth = dashboard?.this_month || {};
  const completionRate = overview.total_orders
    ? Math.round(
        (Number(overview.completed_orders || 0) /
          Number(overview.total_orders)) *
          100,
      )
    : 0;
  const base = `/app/${organizationId}`;

  return (
    <div className="dashboard-page">
      <PageHeader
        eyebrow={new Intl.DateTimeFormat(undefined, {
          weekday: "long",
          day: "numeric",
          month: "long",
        })
          .format(new Date())
          .toUpperCase()}
        title={`${
          new Date().getHours() < 12
            ? "Good morning"
            : new Date().getHours() < 18
              ? "Good afternoon"
              : "Good evening"
        }, ${(user?.full_name || "there").split(" ")[0]}.`}
        description={`Here’s what is happening across ${organization?.name || "your organization"} today.`}
        description={`Here’s what is happening across ${organization?.name || "your organization"} today.`}
        action={
          <div className="date-control">
            <button>Last 30 days</button>
            <button>•••</button>
          </div>
        }
      />
      <section className="metric-strip">
        <div>
          <span>Net revenue</span>
          <strong>{money(Number(overview.total_revenue || 0))}</strong>
          <small>Current completed-order revenue</small>
        </div>
        <div>
          <span>Total orders</span>
          <strong>{overview.total_orders || 0}</strong>
          <small>All orders in this organization</small>
        </div>
        <div>
          <span>Completed</span>
          <strong>{overview.completed_orders || 0}</strong>
          <small>{completionRate}% completion rate</small>
        </div>
        <div className="attention">
          <span>Low stock</span>
          <strong>{overview.low_stock_products || 0}</strong>
          <small>
            {overview.low_stock_products || 0} items require attention
          </small>
        </div>
      </section>
      <section className="dashboard-analytics">
        <div className="revenue-panel">
          <div className="panel-heading">
            <div>
              <span>Revenue trend</span>
              <small>Daily net revenue</small>
            </div>
            <div className="chart-legend">
              <i />
              This period <i />
              Previous
            </div>
          </div>
          <div className="big-chart">
            <div className="axis">
              <span>₦12k</span>
              <span>₦8k</span>
              <span>₦4k</span>
              <span>₦0</span>
            </div>
            <div className="chart-area">
              <i />
              <i />
              <i />
              <i />
              <svg viewBox="0 0 700 220" preserveAspectRatio="none">
                <path
                  className="previous"
                  d="M0 180C50 160 70 170 110 142s75 20 120-8 60-3 105-34 80 7 120-24 70 14 120-30 70 8 125-25"
                />
                <path
                  className="current"
                  d="M0 190C40 185 70 125 110 145s65-40 120-18 65-85 120-58 55 45 110 2 70-25 110-58 75 10 130-2"
                />
                <path
                  className="fill"
                  d="M0 190C40 185 70 125 110 145s65-40 120-18 65-85 120-58 55 45 110 2 70-25 110-58 75 10 130-2v210H0Z"
                />
              </svg>
              <div className="chart-days">
                <span>May 26</span>
                <span>Jun 02</span>
                <span>Jun 09</span>
                <span>Jun 16</span>
                <span>Jun 24</span>
              </div>
            </div>
          </div>
        </div>
        <div className="order-pulse">
          <div className="panel-heading">
            <div>
              <span>Order pulse</span>
              <small>Compared with previous period</small>
            </div>
          </div>
          {[
            ["Today", today.orders || 0, ""],
            ["This week", thisWeek.orders || 0, ""],
            ["This month", thisMonth.orders || 0, ""],
          ].map((x) => (
            <div className="pulse-row" key={x[0]}>
              <span>{x[0]}</span>
              <b>{x[1]}</b>
              <em>{x[2]}</em>
            </div>
          ))}
          <div className="completion">
            <div>
              <span>Completion rate</span>
              <b>{completionRate}%</b>
            </div>
            <i>
              <b />
            </i>
            <small>
              {overview.completed_orders || 0} of {overview.total_orders || 0}{" "}
              orders completed
            </small>
          </div>
        </div>
      </section>
      <section className="dashboard-lists">
        <div className="dash-list orders">
          <div className="panel-heading">
            <div>
              <span>Recent orders</span>
              <small>The latest activity across your orders</small>
            </div>
            <Link to={`${base}/orders`}>View all →</Link>
          </div>
          {orders.slice(0, 4).map((o) => (
            <Link
              to={`${base}/orders/${o.id}`}
              className="dash-order"
              key={o.id}
            >
              <b>{o.number}</b>
              <span>{o.customer}</span>
              <span>{o.date}</span>
              <strong>{money(o.amount)}</strong>
              <Status>{o.status}</Status>
            </Link>
          ))}
        </div>
        <div className="dash-list stock">
          <div className="panel-heading">
            <div>
              <span>Stock attention</span>
              <small>Items at or below their threshold</small>
            </div>
            <Link to={`${base}/inventory`}>View inventory →</Link>
          </div>
          {products
            .filter((p) => p.stock <= p.threshold)
            .map((p) => (
              <div className="stock-row" key={p.id}>
                <div className="product-thumb">{p.name.slice(0, 1)}</div>
                <span>
                  <b>{p.name}</b>
                  <small>
                    {p.sku} · Reorder at {p.threshold}
                  </small>
                </span>
                <strong>
                  {p.stock}
                  <small> units</small>
                </strong>
              </div>
            ))}
        </div>
      </section>
      <section className="activity-feed">
        <div className="panel-heading">
          <div>
            <span>Recent activity</span>
            <small>Important changes in this workspace</small>
          </div>
          <Link to={`${base}/activity`}>Full history →</Link>
        </div>
        <div>
          {activities.slice(0, 4).map((a, i) => (
            <div className="feed-row" key={a.id ?? `${a.action}-${i}`}>
              <i className={`feed-dot d${i}`}>
                <Icon
                  name={
                    a.category === "Order"
                      ? "orders"
                      : String(a.category || "activity").toLowerCase()
                  }
                />
              </i>
              <span>
                <b>{a.action}</b>
                <small>{a.detail}</small>
              </span>
              <span>{a.user}</span>
              <time>{a.time}</time>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export function ProductMockup({ compact = false }) {
  return (
    <div className={`product-window ${compact ? "compact" : ""}`}>
      <div className="window-bar">
        <div className="window-mark">D</div>
        <span>Daymark</span>
        <div className="window-search">
          Search anything <kbd>⌘K</kbd>
        </div>
        <div className="window-user">AM</div>
      </div>
      <div className="product-body">
        <aside className="product-sidebar">
          <b>Workspace</b>
          {["Overview", "Products", "Inventory", "Orders", "Customers"].map(
            (item, i) => (
              <span className={i === 0 ? "active" : ""} key={item}>
                <i />
                {item}
              </span>
            ),
          )}
          <div className="sidebar-foot">
            <span>
              <i />
              Team
            </span>
            <span>
              <i />
              Settings
            </span>
          </div>
        </aside>
        <div className="product-content">
          <div className="product-heading">
            <div>
              <small>MONDAY, 24 JUNE</small>
              <h3>Good morning, Alex.</h3>
            </div>
            <button>+ New order</button>
          </div>
          <div className="metric-row">
            <div>
              <small>NET SALES</small>
              <strong>₦24,680</strong>
              <em>↑ 12.4%</em>
            </div>
            <div>
              <small>ORDERS</small>
              <strong>184</strong>
              <em>↑ 8.2%</em>
            </div>
            <div>
              <small>LOW STOCK</small>
              <strong>12</strong>
              <em className="warn">Needs review</em>
            </div>
          </div>
          <div className="dashboard-grid">
            <div className="chart-card">
              <div className="card-title">
                <span>Sales overview</span>
                <small>Last 7 days</small>
              </div>
              <div className="chart">
                <div className="chart-lines">
                  <i />
                  <i />
                  <i />
                </div>
                <svg viewBox="0 0 500 150" preserveAspectRatio="none">
                  <path
                    className="area"
                    d="M0 135C60 130 80 95 135 105s70-55 125-38 70 53 120 13 70-45 120-63v133H0Z"
                  />
                  <path d="M0 135C60 130 80 95 135 105s70-55 125-38 70 53 120 13 70-45 120-63" />
                </svg>
              </div>
              <div className="chart-labels">
                <span>MON</span>
                <span>TUE</span>
                <span>WED</span>
                <span>THU</span>
                <span>FRI</span>
                <span>SAT</span>
                <span>SUN</span>
              </div>
            </div>
            <div className="stock-card">
              <div className="card-title">
                <span>Inventory health</span>
                <small>420 products</small>
              </div>
              <div className="donut">
                <span>
                  <b>86%</b>
                  <small>healthy</small>
                </span>
              </div>
              <div className="stock-key">
                <span>
                  <i />
                  In stock <b>362</b>
                </span>
                <span>
                  <i />
                  Low stock <b>46</b>
                </span>
                <span>
                  <i />
                  Out of stock <b>12</b>
                </span>
              </div>
            </div>
          </div>
          <div className="orders-card">
            <div className="card-title">
              <span>Recent orders</span>
              <small>View all →</small>
            </div>
            {[
              ["#DM-1084", "North & Pine", "₦1,240.00", "Fulfilled"],
              ["#DM-1083", "Common Goods", "₦680.00", "Processing"],
              ["#DM-1082", "Field Office", "₦2,105.50", "Fulfilled"],
            ].map((row) => (
              <div className="order-row" key={row[0]}>
                {row.map((cell, i) => (
                  <span
                    className={i === 3 ? `status s${row[3]}` : ""}
                    key={cell}
                  >
                    {cell}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

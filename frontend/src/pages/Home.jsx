import { useState } from "react";
import { Link } from "react-router";
import { Arrow, MarkIcon } from "../components/Brand";
import { ProductMockup } from "../features/public/components/ProductMockup";

const capabilities = [
  [
    "01",
    "Products",
    "Keep your catalogue clean, consistent and ready for every order.",
    "products",
  ],
  [
    "02",
    "Inventory",
    "See what is available, what is moving and what needs attention.",
    "inventory",
  ],
  [
    "03",
    "Customers",
    "Keep customer details and order history within easy reach.",
    "customers",
  ],
  [
    "04",
    "Orders",
    "Move every order from creation to completion with less friction.",
    "orders",
  ],
  [
    "05",
    "Insights",
    "Read the pace of the business without assembling another spreadsheet.",
    "insights",
  ],
  [
    "06",
    "Team",
    "Give each person the access they need—and nothing they do not.",
    "team",
  ],
];

const faqs = [
  [
    "What is Daymark?",
    "Daymark is a business operations platform that brings products, inventory, customers, orders and performance visibility into one connected workspace.",
  ],
  [
    "Who can use Daymark?",
    "Daymark is designed for small and medium-sized businesses, including retailers, distributors and growing product-based teams.",
  ],
  [
    "Can I manage multiple businesses?",
    "Daymark is built around separate organisation workspaces. Multi-business availability will depend on your account setup. Contact us to discuss your needs.",
  ],
  [
    "Can I invite employees?",
    "Yes. You can invite team members and control their access with roles and permissions.",
  ],
  [
    "Does Daymark work without internet?",
    "Daymark supports recently loaded information, local drafts and selected queued actions when your connection is unavailable. Not every action is available offline.",
  ],
  [
    "What happens when connectivity returns?",
    "Supported pending actions synchronize automatically. Daymark makes the sync status visible so your team knows what is saved and what still needs attention.",
  ],
  [
    "How do I get started?",
    "Create an account, set up your workspace, add your business information and products, then invite your team.",
  ],
];

export function Home() {
  return (
    <main>
      <section className="hero">
        <div className="hero-grid">
          <div className="hero-copy">
            <p className="hero-kicker">Business operations, made visible.</p>
            <h1>
              Run the day.
              <br />
              <span>See the whole business.</span>
            </h1>
            <p className="hero-lede">
              Products, inventory, customers and orders in one connected
              workspace—so your team can spend less time piecing things
              together.
            </p>
            <div className="button-row">
              <Link className="button button-accent" to="/register">
                Get started <Arrow />
              </Link>
              <Link className="text-link" to="/features">
                Explore the platform <Arrow diagonal />
              </Link>
            </div>
          </div>
          <div className="hero-note">
            <span className="mono">DAYMARK / 01</span>
            <p>A calmer operating system for busy businesses.</p>
          </div>
        </div>
        <div className="hero-product">
          <div className="product-glow" />
          <ProductMockup />
          <div className="float-note sync-note">
            <i />
            All changes synced <span>Just now</span>
          </div>
          <div className="float-note stock-note">
            <small>STOCK ALERT</small>
            <b>12 items</b>
            <span>need review</span>
          </div>
        </div>
      </section>

      <section className="intro section">
        <div className="section-label">
          <span>01</span>
          <p>One workspace</p>
        </div>
        <div className="intro-copy">
          <h2>
            Your business is connected.
            <br />
            Your tools should be too.
          </h2>
          <div className="intro-body">
            <p>
              Orders affect stock. Products shape customer decisions. Team
              activity changes what happens next. Daymark keeps those moving
              parts in view, together.
            </p>
            <p>
              No patchwork of tabs. No hand-built status report. Just a shared,
              dependable picture of the business as the day unfolds.
            </p>
          </div>
        </div>
      </section>

      <section className="capabilities section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">WHAT DAYMARK BRINGS TOGETHER</span>
            <h2>
              Every moving part,
              <br />
              in its place.
            </h2>
          </div>
          <p>
            Designed around the real relationships between the work—not a
            collection of disconnected features.
          </p>
        </div>
        <div className="capability-list">
          {capabilities.map(([n, title, copy, icon]) => (
            <Link to="/features" className="capability-row" key={title}>
              <span className="mono">{n}</span>
              <MarkIcon name={icon} />
              <h3>{title}</h3>
              <p>{copy}</p>
              <Arrow diagonal />
            </Link>
          ))}
        </div>
      </section>

      <section className="offline-section">
        <div className="offline-copy">
          <span className="eyebrow text-sage">BUILT FOR THE REAL WORLD</span>
          <h2>
            The work keeps moving.
            <br />
            Even when the signal doesn’t.
          </h2>
          <p>
            Daymark is designed for businesses where connectivity is not always
            guaranteed. Keep useful information close, prepare work offline, and
            let supported changes synchronize when you reconnect.
          </p>
          <ul>
            <li>Access recently loaded information</li>
            <li>Save local drafts while offline</li>
            <li>Queue supported actions safely</li>
            <li>See when pending work has synchronized</li>
          </ul>
          <p className="offline-caveat">
            Offline availability varies by action. Daymark always shows what is
            local, pending or fully synchronized.
          </p>
        </div>
        <SyncDemo />
      </section>

      <section className="workflow section">
        <div className="section-label">
          <span>02</span>
          <p>Getting started</p>
        </div>
        <div className="section-heading compact-heading">
          <h2>
            From sign-up to
            <br />a working workspace.
          </h2>
          <p>
            A deliberate setup flow gets the important foundations in place
            without slowing you down.
          </p>
        </div>
        <ol className="steps">
          {[
            "Create your account",
            "Set up your workspace",
            "Add products and business details",
            "Invite your team",
            "Run your operations",
          ].map((step, i) => (
            <li key={step}>
              <span className="step-number">0{i + 1}</span>
              <b>{step}</b>
              <i />
            </li>
          ))}
        </ol>
      </section>

      <section className="audience">
        <div className="audience-heading">
          <span className="eyebrow">WHO IT’S FOR</span>
          <h2>
            Built for businesses
            <br />
            with a lot in motion.
          </h2>
        </div>
        <div className="audience-grid">
          <article>
            <span>Retail</span>
            <h3>Keep stock and sales moving together.</h3>
            <p>
              Make product availability, customer context and order progress
              easier to follow from opening to close.
            </p>
          </article>
          <article>
            <span>Distribution</span>
            <h3>Stay ahead of orders and inventory.</h3>
            <p>
              Give teams a shared view of what has been ordered, what is
              available and what needs action.
            </p>
          </article>
          <article>
            <span>Growing teams</span>
            <h3>Replace workarounds with a clear process.</h3>
            <p>
              Bring scattered operational work into a system that can grow with
              your people and volume.
            </p>
          </article>
        </div>
        <Link className="button button-light" to="/solutions">
          Explore solutions <Arrow />
        </Link>
      </section>

      <section className="security section">
        <div>
          <span className="eyebrow">CONTROL WITHOUT COMPLEXITY</span>
          <h2>Your business information stays with your business.</h2>
        </div>
        <div className="security-grid">
          <div>
            <b>Separate by organisation</b>
            <p>
              Each workspace keeps its own business data and operating context
              distinct.
            </p>
          </div>
          <div>
            <b>Roles and permissions</b>
            <p>
              Control what team members can see and do based on their
              responsibilities.
            </p>
          </div>
          <div>
            <b>Secure access</b>
            <p>
              Authentication and controlled access help protect business
              information.
            </p>
          </div>
          <div>
            <b>Visible activity</b>
            <p>
              Understand important changes and keep responsibility clear across
              the team.
            </p>
          </div>
        </div>
      </section>

      <section className="faq section">
        <div className="faq-heading">
          <span className="eyebrow">THE DETAILS</span>
          <h2>
            Questions,
            <br />
            answered clearly.
          </h2>
          <p>Still deciding if Daymark fits the way you work?</p>
          <Link className="text-link" to="/contact">
            Talk to us <Arrow diagonal />
          </Link>
        </div>
        <div className="faq-list">
          {faqs.map(([q, a]) => (
            <Faq key={q} q={q} a={a} />
          ))}
        </div>
      </section>

      <section className="final-cta">
        <div>
          <span className="eyebrow text-sage">YOUR NEXT WORKING DAY</span>
          <h2>Start with a clearer view.</h2>
        </div>
        <p>
          Bring the operational essentials into one place and give your team a
          better way to move the day forward.
        </p>
        <Link className="button button-accent" to="/register">
          Create your account <Arrow />
        </Link>
      </section>
    </main>
  );
}

function SyncDemo() {
  const [online, setOnline] = useState(false);
  return (
    <div className={`sync-demo ${online ? "online" : ""}`}>
      <div className="sync-top">
        <div>
          <i />
          <span>{online ? "Connection restored" : "Working offline"}</span>
        </div>
        <button onClick={() => setOnline(!online)}>
          {online ? "Go offline" : "Restore connection"}
        </button>
      </div>
      <div className="sync-date">
        TODAY <span>3 PENDING</span>
      </div>
      {[
        ["New order", "North & Pine · 8 items"],
        ["Inventory count", "Warehouse A · 24 updates"],
        ["Customer note", "Common Goods"],
      ].map((item, i) => (
        <div className="sync-item" key={item[0]}>
          <div className="sync-icon">{online ? "✓" : i + 1}</div>
          <div>
            <b>{item[0]}</b>
            <span>{item[1]}</span>
          </div>
          <em>{online ? "Synced" : "Queued"}</em>
        </div>
      ))}
      <div className="sync-progress">
        <div>
          <span>
            {online
              ? "Everything is up to date"
              : "Changes saved on this device"}
          </span>
          <span>{online ? "100%" : "Waiting for connection"}</span>
        </div>
        <i />
      </div>
    </div>
  );
}

function Faq({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`faq-item ${open ? "open" : ""}`}>
      <button onClick={() => setOpen(!open)} aria-expanded={open}>
        <span>{q}</span>
        <i>{open ? "−" : "+"}</i>
      </button>
      <div>
        <p>{a}</p>
      </div>
    </div>
  );
}

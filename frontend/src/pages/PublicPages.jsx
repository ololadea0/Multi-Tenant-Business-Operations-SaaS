import { useState } from "react"
import { Link } from "react-router"
import { Arrow, MarkIcon } from "../components/Brand"
import { ProductMockup } from "../components/ProductMockup"

const featureData = [
  [
    "Products",
    "A catalogue your whole operation can rely on.",
    "Keep product names, pricing, identifiers and status consistent. Make updates once and give every order and inventory decision a dependable starting point.",
    "products",
  ],
  [
    "Inventory",
    "Know what you have—and what needs action.",
    "Follow availability across your operation, spot low stock early and understand how inventory changes as orders move.",
    "inventory",
  ],
  [
    "Customers",
    "Keep useful context close to every order.",
    "Organise customer information and order history so your team can respond with the right context, without searching across systems.",
    "customers",
  ],
  [
    "Orders",
    "A clearer path from request to completion.",
    "Create, review and progress orders from one shared view. Status stays visible, ownership stays clear and stock stays connected.",
    "orders",
  ],
  [
    "Business insights",
    "See the shape of the day at a glance.",
    "Read key sales, order and inventory signals in a focused overview designed for useful decisions—not dashboard theatre.",
    "insights",
  ],
  [
    "Team access",
    "Give the right people the right view.",
    "Invite your team, assign roles and keep access aligned with each person’s responsibilities as your business grows.",
    "team",
  ],
]

function PageHero({
  label,
  title,
  copy,
  action,
}) {
  return (
    <section className="page-hero">
      <span className="eyebrow">{label}</span>
      <h1>{title}</h1>
      <p>{copy}</p>
      {action && (
        <Link className="button button-accent" to="/register">
          Get started <Arrow />
        </Link>
      )}
    </section>
  )
}

export function Features() {
  return (
    <main>
      <PageHero
        label="THE PLATFORM"
        title={
          <>
            One connected view of
            <br />
            the work that matters.
          </>
        }
        copy="Daymark brings the operational essentials together, so each part of your business can inform the next."
        action
      />
      <section className="feature-showcase">
        <ProductMockup compact />
      </section>
      <section className="feature-details section">
        {featureData.map(([name, title, copy, icon], i) => (
          <article className="feature-detail" key={name}>
            <div className="feature-number">
              <span>0{i + 1}</span>
              <MarkIcon name={icon} />
            </div>
            <div>
              <span className="eyebrow">{name}</span>
              <h2>{title}</h2>
              <p>{copy}</p>
            </div>
            <FeatureVisual type={icon} />
          </article>
        ))}
      </section>
      <section className="mini-cta">
        <h2>Ready for a clearer working day?</h2>
        <Link className="button button-accent" to="/register">
          Create your account <Arrow />
        </Link>
      </section>
    </main>
  )
}

function FeatureVisual({ type }) {
  return (
    <div className={`feature-visual ${type}`}>
      <div className="visual-header">
        <span>Daymark / {type}</span>
        <i>•••</i>
      </div>
      {type === "inventory" ? (
        <>
          <div className="inventory-bars">
            {[76, 48, 92, 31].map((n, i) => (
              <div key={i}>
                <span>Item 0{i + 1}</span>
                <i>
                  <b style={{ width: `${n}%` }} />
                </i>
                <em>{n}</em>
              </div>
            ))}
          </div>
        </>
      ) : type === "insights" ? (
        <div className="mini-chart">
                <b>₦24,680</b>
          <span>NET SALES / 7 DAYS</span>
          <svg viewBox="0 0 300 100">
            <path d="M0 85C45 80 45 35 90 55s45 20 80-12 55 5 130-38" />
          </svg>
        </div>
      ) : (
        <div className="visual-rows">
          {["Primary record", "Connected detail", "Recent activity"].map(
            (x, i) => (
              <div key={x}>
                <i className={`avatar a${i}`} />
                <span>
                  <b>{x}</b>
                  <small>Updated today</small>
                </span>
                <em>{i === 0 ? "Active" : "View"}</em>
              </div>
            ),
          )}
        </div>
      )}
    </div>
  )
}

export function Solutions() {
  const scenarios = [
    [
      "Retail businesses",
      "A clear view from shelf to sale.",
      "Keep product details, stock levels, customer information and orders aligned through the trading day.",
      [
        "Review low-stock items before opening",
        "Create and track customer orders",
        "Give staff access based on their role",
      ],
    ],
    [
      "Distributors",
      "Order movement without the blind spots.",
      "Bring order status and inventory availability into the same working view so the team can act with better context.",
      [
        "Confirm availability as orders arrive",
        "Track progress through fulfilment",
        "Keep customer order history accessible",
      ],
    ],
    [
      "Growing businesses",
      "Structure that grows with the work.",
      "Replace improvised spreadsheets and scattered tools with a shared operational foundation for a growing team.",
      [
        "Standardise essential product data",
        "Create repeatable operating workflows",
        "Keep responsibility and access clear",
      ],
    ],
  ]
  return (
    <main>
      <PageHero
        label="PRACTICAL BY DESIGN"
        title={
          <>
            Different businesses.
            <br />
            The same need for clarity.
          </>
        }
        copy="Daymark supports product-based businesses with practical tools for the operational work they already do."
        action
      />
      <section className="scenario-list section">
        {scenarios.map((s, i) => (
          <article key={s[0]}>
            <div className="scenario-index">0{i + 1}</div>
            <div>
              <span className="eyebrow">{s[0]}</span>
              <h2>{s[1]}</h2>
              <p>{s[2]}</p>
            </div>
            <ul>
              {(s[3]).map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
          </article>
        ))}
      </section>
      <section className="solution-banner">
        <div>
          <span className="eyebrow text-sage">YOUR WAY OF WORKING</span>
          <h2>Have a more specific operating model?</h2>
        </div>
        <p>
          Tell us how your team works today. We’ll help you understand where
          Daymark fits—and where it does not.
        </p>
        <Link className="button button-light" to="/contact">
          Contact us <Arrow />
        </Link>
      </section>
    </main>
  )
}

export function About() {
  return (
    <main>
      <PageHero
        label="ABOUT DAYMARK"
        title={
          <>
            Make the business
            <br />
            easier to read.
          </>
        }
        copy="Daymark exists to give growing teams a clearer, calmer way to manage the operational details that shape every working day."
      />
      <section className="about-statement">
        <span>Our purpose</span>
        <p>
          Good operations rarely look dramatic. They look like the right stock
          in the right place, an order moving on time, a team that knows what to
          do next, and a business owner who can see the full picture.
        </p>
      </section>
      <section className="principles section">
        <div className="section-label">
          <span>01</span>
          <p>Our principles</p>
        </div>
        <div className="principle-grid">
          <article>
            <b>Clarity over clutter</b>
            <p>
              We reduce the effort it takes to understand what is happening and
              what needs attention.
            </p>
          </article>
          <article>
            <b>Practical by default</b>
            <p>
              Every feature should solve a real operating problem, not simply
              add to a list.
            </p>
          </article>
          <article>
            <b>Continuity matters</b>
            <p>
              Work should remain resilient when the network, the day or the plan
              becomes unpredictable.
            </p>
          </article>
          <article>
            <b>Trust is designed in</b>
            <p>
              Clear access, visible status and honest product language are
              foundational—not finishing touches.
            </p>
          </article>
        </div>
      </section>
      <section className="mini-cta">
        <h2>See what Daymark can bring together.</h2>
        <Link className="button button-accent" to="/features">
          Explore the platform <Arrow />
        </Link>
      </section>
    </main>
  )
}

export function Contact() {
  const [sent, setSent] = useState(false)
  function submit(e) {
    e.preventDefault()
    setSent(true)
  }
  return (
    <main className="contact-page">
      <section className="contact-intro">
        <span className="eyebrow">CONTACT DAYMARK</span>
        <h1>
          Tell us what your
          <br />
          business needs.
        </h1>
        <p>
          Whether you are evaluating Daymark or have a specific question, we’ll
          point you in the right direction.
        </p>
        <div className="contact-meta">
          <span>
            <b>General enquiries</b>hello@daymark.example
          </span>
          <span>
            <b>Response time</b>Usually within 2 business days
          </span>
          <small>Contact details are placeholders.</small>
        </div>
      </section>
      <section className="contact-form-wrap">
        {sent ? (
          <div className="form-success">
            <span>✓</span>
            <h2>Message received.</h2>
            <p>
              Thanks for getting in touch. We’ll respond using the email address
              you provided.
            </p>
            <button className="text-link" onClick={() => setSent(false)}>
              Send another message <Arrow />
            </button>
          </div>
        ) : (
          <form className="contact-form" onSubmit={submit}>
            <div className="field-row">
              <label>
                First name
                <input required name="firstName" autoComplete="given-name" />
              </label>
              <label>
                Last name
                <input required name="lastName" autoComplete="family-name" />
              </label>
            </div>
            <label>
              Work email
              <input required type="email" name="email" autoComplete="email" />
            </label>
            <label>
              Business name
              <input name="business" autoComplete="organization" />
            </label>
            <label>
              What would you like to discuss?
              <select name="topic" defaultValue="">
                <option value="" disabled>
                  Select a topic
                </option>
                <option>Using Daymark</option>
                <option>Account setup</option>
                <option>Partnership</option>
                <option>Something else</option>
              </select>
            </label>
            <label>
              Message
              <textarea
                required
                name="message"
                rows={5}
                placeholder="Tell us a little about your business and what you need."
              />
            </label>
            <button className="button button-dark" type="submit">
              Send enquiry <Arrow />
            </button>
          </form>
        )}
      </section>
    </main>
  )
}

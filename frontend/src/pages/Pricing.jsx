import { useState } from "react"
import { Link } from "react-router"
import { usePlansQuery } from "../app/store/api"

const naira = (amount) => new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(amount)

export function Pricing() {
  const [interval, setInterval] = useState("monthly")
  const { data: plans = [], isLoading, error } = usePlansQuery()
  return <main className="pricing-page">
    <section className="page-hero"><span className="eyebrow">PRICING</span><h1>Every plan includes the full Daymark platform.</h1><p>Choose the capacity that fits your operation. Plans differ by usage limits, not essential modules.</p><div><button className={interval === "monthly" ? "button button-accent" : "button"} onClick={() => setInterval("monthly")}>Monthly</button><button className={interval === "annual" ? "button button-accent" : "button"} onClick={() => setInterval("annual")}>Annual · 2 months free</button></div></section>
    <section className="pricing-grid">{isLoading && <p>Loading plans…</p>}{error && <p>Plans are temporarily unavailable.</p>}{plans.map((plan) => <article className="pricing-card" key={plan.key}><span className="eyebrow">{plan.name}</span><h2>{naira(interval === "monthly" ? plan.monthly_price : plan.annual_price)}<small>/{interval === "monthly" ? "month" : "year"}</small></h2><p>{plan.description}</p><ul><li>Full dashboard, products, inventory, customers and orders</li><li>Up to {plan.max_team_members} team members</li><li>Up to {plan.max_products} products</li><li>Up to {plan.max_monthly_orders} orders per month</li></ul><Link className="button button-accent" to={`/register?plan=${plan.key}&interval=${interval}`}>Choose {plan.name}</Link></article>)}</section>
  </main>
}

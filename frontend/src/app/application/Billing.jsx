import { useState } from "react"
import { useParams } from "react-router"
import { useBillingHistoryQuery, useBillingQuery, useCancelSubscriptionMutation, useInitializeCheckoutMutation, usePlansQuery } from "../store/api"
import { Notice, PageHeader, Status } from "./Ui"

const money = (value, currency = "NGN") => new Intl.NumberFormat("en-NG", { style: "currency", currency, maximumFractionDigits: 0 }).format(Number(value || 0))
const date = (value) => value ? new Date(value).toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" }) : "—"

export function Billing() {
  const { organizationId } = useParams()
  const { data: billing, isLoading, error } = useBillingQuery(organizationId, { skip: !organizationId })
  const { data: history = [] } = useBillingHistoryQuery(organizationId, { skip: !organizationId })
  const { data: plans = [] } = usePlansQuery()
  const [initializeCheckout, checkoutState] = useInitializeCheckoutMutation()
  const [cancelSubscription, cancelState] = useCancelSubscriptionMutation()
  const [interval, setInterval] = useState("monthly")
  const [selectedPlan, setSelectedPlan] = useState(null)
  const usage = billing?.usage || {}
  const plan = billing?.plan
  const meters = [["Team members", usage.team_members, plan?.max_team_members], ["Products", usage.products, plan?.max_products], ["Orders this month", usage.monthly_orders, plan?.max_monthly_orders]]
  async function startCheckout() {
    if (!selectedPlan) return
    const result = await initializeCheckout({ organizationId, plan_key: selectedPlan.key, interval }).unwrap()
    if (result.authorization_url) window.location.assign(result.authorization_url)
  }
  async function cancel() {
    if (window.confirm("Cancel automatic renewal for this subscription? Your existing business data will remain available.")) await cancelSubscription(organizationId)
  }
  if (isLoading) return <><PageHeader eyebrow="ORGANIZATION BILLING" title="Billing & Plan" description="Your subscription and payment details." /><div className="billing-loading">Loading your billing details…</div></>
  if (error) return <><PageHeader eyebrow="ORGANIZATION BILLING" title="Billing & Plan" description="Your subscription and payment details." /><Notice tone="error">We could not load billing details. Please try again.</Notice></>
  return <div className="billing-page"><PageHeader eyebrow="ORGANIZATION BILLING" title="Billing & Plan" description="Understand your plan, usage and payments in one place." />
    {billing?.status === "trialing" && <Notice tone="info">You’re enjoying your free trial until {date(billing.trial_end)}. Choose a plan before it ends to continue without interruption.</Notice>}
    <section className="billing-current"><div><span className="billing-kicker">YOUR CURRENT PLAN</span><h2>{plan?.name || "No plan"}</h2><Status>{billing?.status || "unknown"}</Status></div><div className="billing-price">{billing?.status === "trialing" ? <><strong>Free trial</strong><small>Ends {date(billing.trial_end)}</small></> : <><strong>{money(interval === "annual" ? plan?.annual_price : plan?.monthly_price, plan?.currency)}</strong><small>per {billing?.billing_interval || interval}</small></>}</div><div className="billing-next"><span>Next payment</span><b>{billing?.status === "trialing" ? "No payment scheduled" : date(billing?.current_period_end)}</b></div></section>
    <section className="billing-section"><div className="billing-section-head"><div><h2>Your plan usage</h2><p>Your limits determine how much your business can manage.</p></div></div><div className="billing-meters">{meters.map(([label, current, maximum]) => { const used = Number(current || 0); const limit = Number(maximum || 0); const percent = limit ? Math.min(100, Math.round(used / limit * 100)) : 0; return <div className="billing-meter" key={label}><div><b>{label}</b><span>{used.toLocaleString()} of {limit.toLocaleString()} used</span></div><div className="billing-progress"><i style={{ width: `${percent}%` }} /></div><small>{limit ? `${Math.max(0, limit - used).toLocaleString()} remaining` : "Not available"}</small></div> })}</div></section>
    <section className="billing-section"><div className="billing-section-head"><div><h2>Available plans</h2><p>All plans include Daymark’s core modules. Choose the limits that fit your business.</p></div><div className="billing-toggle"><button className={interval === "monthly" ? "active" : ""} onClick={() => setInterval("monthly")}>Monthly</button><button className={interval === "annual" ? "active" : ""} onClick={() => setInterval("annual")}>Annual</button></div></div><div className="billing-plans">{plans.map((item) => { const isCurrent = billing?.status === "active" && item.key === plan?.key; return <article className={isCurrent ? "billing-plan current" : "billing-plan"} key={item.key}><span className="billing-kicker">{item.name}</span><strong>{money(interval === "annual" ? item.annual_price : item.monthly_price)}</strong><small>per {interval === "annual" ? "year" : "month"}</small><p>{item.description}</p><ul><li>{item.max_team_members} team members</li><li>{item.max_products} products</li><li>{item.max_monthly_orders} monthly orders</li></ul><button className="app-btn secondary" disabled={isCurrent} onClick={() => setSelectedPlan(item)}>{isCurrent ? "Current plan" : "Choose plan"}</button></article> })}</div></section>
    <section className="billing-section"><div className="billing-section-head"><div><h2>Payment history</h2><p>Your payments returned by Paystack.</p></div></div><div className="billing-history">{history.length ? history.map((payment) => <div className="billing-payment" key={payment.reference}><span><b>{payment.reference}</b><small>{date(payment.created_at)} · {payment.interval}</small></span><Status>{payment.status}</Status><strong>{money(payment.amount, payment.currency)}</strong></div>) : <p className="billing-empty">No payments have been recorded yet.</p>}</div></section>
    <section className="billing-manage"><div><h2>Manage subscription</h2><p>Changing plans keeps your existing business records. Cancellation stops future renewal; your access policy is managed by the backend.</p></div><button className="app-btn secondary" onClick={cancel} disabled={cancelState.isLoading || billing?.status === "cancelled"}>{cancelState.isLoading ? "Cancelling…" : billing?.status === "cancelled" ? "Subscription cancelled" : "Cancel subscription"}</button></section>
    {selectedPlan && <div className="dialog-layer"><button className="dialog-scrim" onClick={() => setSelectedPlan(null)} /><div className="app-dialog billing-confirm"><h2>Change to {selectedPlan.name}?</h2><p>Your new subscription will cost {money(interval === "annual" ? selectedPlan.annual_price : selectedPlan.monthly_price)} per {interval === "annual" ? "year" : "month"}. Existing business records will remain available.</p>{checkoutState.error && <Notice tone="error">Payment could not be started. Please try again.</Notice>}<footer><button className="app-btn secondary" onClick={() => setSelectedPlan(null)}>Go back</button><button className="app-btn primary" onClick={startCheckout} disabled={checkoutState.isLoading}>{checkoutState.isLoading ? "Opening checkout…" : "Continue to payment"}</button></footer></div></div>}
  </div>
}

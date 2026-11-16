import { useParams } from "react-router"
import { useActivitiesQuery, useCustomersQuery, useDashboardQuery, useInventoryQuery, useMeQuery, useMembersQuery, useOrdersQuery, useProductsQuery } from "./api"
import { offlineDb } from "./db"
import { useEffect, useState } from "react"

const unwrap = (value) => Array.isArray(value) ? value : value?.items || []

const formatWatDate = (value, mode = "datetime") => {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "—"
  const options = mode === "date"
    ? { timeZone: "Africa/Lagos", dateStyle: "short" }
    : { timeZone: "Africa/Lagos", dateStyle: "short", timeStyle: "short" }
  return new Intl.DateTimeFormat("en-NG", options).format(date)
}

export function useOfflineQueue(organizationId) {
  const [operations, setOperations] = useState([])
  useEffect(() => {
    if (!organizationId) return undefined
    let active = true
    const refresh = () => offlineDb.operations.where("organizationId").equals(organizationId).toArray().then((items) => active && setOperations(items))
    refresh()
    const timer = window.setInterval(refresh, 5000)
    return () => { active = false; window.clearInterval(timer) }
  }, [organizationId])
  return operations
}

export function useOrganizationData() {
  const { organizationId } = useParams()
  const productsQuery = useProductsQuery(organizationId, { skip: !organizationId })
  const customersQuery = useCustomersQuery(organizationId, { skip: !organizationId })
  const ordersQuery = useOrdersQuery(organizationId, { skip: !organizationId })
  const inventoryQuery = useInventoryQuery(organizationId, { skip: !organizationId })
  const dashboardQuery = useDashboardQuery(organizationId, { skip: !organizationId })
  const activitiesQuery = useActivitiesQuery(organizationId, { skip: !organizationId })
  const membersQuery = useMembersQuery(organizationId, { skip: !organizationId })
  const meQuery = useMeQuery()
  const currentUserId = meQuery.data?.id
  const currentUserEmail = meQuery.data?.email?.toLowerCase()
  const products = unwrap(productsQuery.data).map((product) => ({ ...product, stock: product.stock_quantity, threshold: product.low_stock_threshold, price: Number(product.unit_price || 0), cost: Number(product.cost_price || 0), status: product.status || "ACTIVE" }))
  const customers = unwrap(customersQuery.data).map((customer) => ({
    ...customer,
    orders: customer.order_count || 0,
    added: customer.created_at ? formatWatDate(customer.created_at, "date") : "—",
    joined: customer.created_at ? formatWatDate(customer.created_at, "date") : "—",
  }))
  const orders = unwrap(ordersQuery.data).map((order) => ({ ...order, number: order.order_number, amount: Number(order.total_amount || 0), customer: order.customer_id, date: order.created_at ? formatWatDate(order.created_at, "date") : "—" }))
  const movements = unwrap(inventoryQuery.data).map((movement) => ({ ...movement, product: movement.product_name || products.find((item) => item.id === movement.product_id)?.name || `Product #${movement.product_id}`, type: String(movement.movement_type || "").toUpperCase(), date: movement.created_at ? formatWatDate(movement.created_at) : "—", previous: movement.previous_stock, current: movement.new_stock, user: movement.recorded_by || (movement.user_id ? `User #${movement.user_id}` : "Unknown") }))
  const activities = unwrap(activitiesQuery.data).map((activity) => ({
    ...activity,
    category: activity.category || activity.entity_type || "activity",
    detail: activity.detail || activity.description || "",
    user: activity.user_name || activity.user || (activity.user_id ? `User #${activity.user_id}` : "System"),
    time: activity.time || (activity.created_at ? formatWatDate(activity.created_at) : "—"),
  }))
  const team = unwrap(membersQuery.data).map((member) => {
    const isMe = member.user_id === currentUserId || member.email?.toLowerCase() === currentUserEmail
    const lastActive = member.last_active ? new Date(member.last_active) : null
    return {
      ...member,
      isMe,
      name: member.full_name,
      initials: member.full_name?.split(" ").map((part) => part[0]).join("").slice(0, 2),
      status: "Active",
      last: lastActive && !Number.isNaN(lastActive.getTime())
        ? new Intl.DateTimeFormat(undefined, { dateStyle: "short", timeStyle: "short" }).format(lastActive)
        : "—",
    }
  })
  const queries = [productsQuery, customersQuery, ordersQuery, inventoryQuery, dashboardQuery, activitiesQuery, membersQuery, meQuery]
  return { organizationId, products, customers, orders, movements, activities, team, dashboard: dashboardQuery.data, isLoading: queries.some((query) => query.isLoading), error: queries.find((query) => query.error)?.error }
}

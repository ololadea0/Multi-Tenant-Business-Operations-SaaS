import { offlineDb } from "./db"
import { syncStateChanged } from "./slices"

const apiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

export const QUEUEABLE_OPERATIONS = new Set(["customer.create", "customer.update", "product.create", "product.update"])

export async function enqueueOperation({ organizationId, type, resource, resourceId = null, payload, baseVersion = 0 }) {
  if (!QUEUEABLE_OPERATIONS.has(type)) throw new Error(`${type} cannot be queued safely with the current backend`)
  const operation = { operationId: crypto.randomUUID(), organizationId, type, resource, resourceId, payload, baseVersion, createdAt: new Date().toISOString(), status: "pending", retryCount: 0, lastError: null }
  await offlineDb.operations.add(operation)
  return operation
}

export async function clearOrganizationOfflineData(organizationId) {
  await offlineDb.transaction("rw", offlineDb.records, offlineDb.drafts, offlineDb.operations, async () => {
    await offlineDb.records.where("organizationId").equals(organizationId).delete()
    await offlineDb.drafts.where("organizationId").equals(organizationId).delete()
    await offlineDb.operations.where("organizationId").equals(organizationId).and((item) => item.status === "synchronized").delete()
  })
}

export async function saveDraft({ id = crypto.randomUUID(), organizationId, resource, payload }) {
  const draft = { id, organizationId, resource, payload, updatedAt: new Date().toISOString() }
  await offlineDb.drafts.put(draft)
  return draft
}

export async function getDrafts(organizationId, resource) {
  return offlineDb.drafts.where({ organizationId, resource }).toArray()
}

export async function syncPendingOperations({ organizationId, token, dispatch }) {
  const pending = await offlineDb.operations.where("organizationId").equals(organizationId).and((item) => ["pending", "failed"].includes(item.status)).sortBy("createdAt")
  if (!pending.length) return { accepted: 0, conflicts: 0 }
  dispatch?.(syncStateChanged({ state: "synchronizing", pending: pending.length }))
  const operations = pending.map((item) => ({ operation_id: item.operationId, entity_type: item.resource, entity_id: item.resourceId || 0, action: item.type.split(".")[1], base_version: item.baseVersion, payload: item.payload }))
  try {
    const response = await fetch(`${apiUrl}/api/organizations/${organizationId}/sync/push`, { method: "POST", credentials: "include", headers: { "content-type": "application/json", ...(token ? { authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify({ operations }) })
    if (response.status === 409) {
      await offlineDb.operations.where("organizationId").equals(organizationId).and((item) => pending.some((queued) => queued.operationId === item.operationId)).modify({ status: "conflict", lastError: "Server version changed" })
      dispatch?.(syncStateChanged({ state: "conflict", conflicts: pending.length, message: "Review the conflicting changes before retrying." }))
      return { accepted: 0, conflicts: pending.length }
    }
    if (!response.ok) throw new Error(`Sync failed (${response.status})`)
    const result = await response.json()
    const accepted = new Set(result.results.filter((item) => ["queued", "duplicate"].includes(item.status)).map((item) => item.operation_id))
    await offlineDb.operations.where("organizationId").equals(organizationId).and((item) => accepted.has(item.operationId)).modify({ status: "synchronized", syncedAt: new Date().toISOString() })
    dispatch?.(syncStateChanged({ state: "synchronized", pending: Math.max(0, pending.length - accepted.size), lastSyncedAt: new Date().toISOString(), message: "Accepted by the sync service; business application remains server-controlled." }))
    return { accepted: accepted.size, conflicts: 0 }
  } catch (error) {
    await offlineDb.operations.where("organizationId").equals(organizationId).and((item) => pending.some((queued) => queued.operationId === item.operationId)).modify((item) => ({ status: "failed", retryCount: item.retryCount + 1, lastError: error.message }))
    dispatch?.(syncStateChanged({ state: "failed", failed: pending.length, message: error.message }))
    return { accepted: 0, conflicts: 0, failed: pending.length }
  }
}

export function startConnectivityMonitor(store) {
  let probeInFlight = false
  const probe = async () => {
    if (probeInFlight) return
    probeInFlight = true
    const organizationId = store.getState().organization.selectedId
    try {
      const token = store.getState().auth.token || localStorage.getItem("daymark.accessToken")
      const response = await fetch(organizationId ? `${apiUrl}/api/organizations/${organizationId}/sync/status` : `${apiUrl}/health/db`, { credentials: "include", headers: token ? { authorization: `Bearer ${token}` } : {} })
      const reachable = Boolean(response && (response.ok || [401, 403].includes(response.status)))
      store.dispatch(syncStateChanged({ state: reachable ? "online" : "offline" }))
      if (reachable) store.dispatch({ type: "daymark/syncRequested" })
    } catch { store.dispatch(syncStateChanged({ state: "offline" })) } finally { probeInFlight = false }
  }
  window.addEventListener("online", probe)
  window.addEventListener("offline", () => store.dispatch(syncStateChanged({ state: "offline" })))
  probe()
  return () => { window.removeEventListener("online", probe); window.removeEventListener("offline", probe) }
}

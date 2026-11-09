# Daymark offline architecture

The frontend uses Redux Toolkit for shared client state and RTK Query for server data. Dexie persists organization-scoped query results, drafts, and queued operations in IndexedDB.

The backend currently accepts idempotent records at `POST /api/organizations/{organization_id}/sync/push`, checks `base_version`, and exposes changes/status. It does **not** execute the queued payload against products, customers, orders, or inventory. Consequently the client only permits customer/product metadata operations in the queue; order creation, order cancellation, completion, and inventory movements remain online-only until the backend provides an atomic business-operation replay endpoint. This avoids duplicate stock deductions when an order request is retried.

Connectivity is probed through the organization sync-status endpoint. Browser online events are only triggers for that probe, never proof of backend reachability. Network failures are retried through the persistent queue, while 409 responses become conflicts requiring attention. Cached records are presented as last-known data and are never marked as confirmed queued mutations.

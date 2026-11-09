import Dexie from "dexie"

export const offlineDb = new Dexie("daymark-offline")

offlineDb.version(1).stores({
  records: "[organizationId+resource+id], organizationId, resource, updatedAt",
  drafts: "id, organizationId, resource, updatedAt",
  operations: "operationId, organizationId, status, createdAt, resource",
  metadata: "key",
})

export const cacheKey = (organizationId, resource, id = "collection") =>
  `${organizationId}:${resource}:${id}`

export async function cacheCollection(organizationId, resource, value) {
  await offlineDb.records.put({
    organizationId,
    resource,
    id: "collection",
    value,
    updatedAt: new Date().toISOString(),
  })
}

export async function readCachedCollection(organizationId, resource) {
  const record = await offlineDb.records.get([organizationId, resource, "collection"])
  return record?.value
}


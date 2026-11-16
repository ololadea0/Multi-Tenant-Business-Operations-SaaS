import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react"
import { cacheCollection, readCachedCollection } from "./db"
import { organizationCleared, signedOut } from "./slices"

let refreshRequest = null

const rawBaseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000",
  credentials: "include",
  prepareHeaders: (headers, { getState }) => {
    const token = localStorage.getItem("daymark.accessToken") || getState().auth.token
    if (token) headers.set("authorization", `Bearer ${token}`)
    return headers
  },
})

const authenticatedBaseQuery = async (args, api, extraOptions) => {
  let result = await rawBaseQuery(args, api, extraOptions)
  if (result.error?.status === 401 && !String(typeof args === "string" ? args : args.url).includes("/auth/refresh"))
  {
    refreshRequest ||= rawBaseQuery({ url: "/api/auth/refresh", method: "POST" }, api, extraOptions)
    const refresh = await refreshRequest
    refreshRequest = null
    if (refresh.data?.access_token)
    {
      localStorage.setItem("daymark.accessToken", refresh.data.access_token)
      result = await rawBaseQuery(args, api, extraOptions)
    } else
    {
      localStorage.removeItem("daymark.accessToken")
      api.dispatch(signedOut())
      api.dispatch(organizationCleared())
      if (window.location.pathname.startsWith("/app")) window.location.assign("/login")
    }
  }
  return result
}

const offlineBaseQuery = async (args, api, extraOptions) => {
  const result = await authenticatedBaseQuery(args, api, extraOptions)
  if (!result.error)
  {
    const organizationId = api.getState().organization.selectedId
    if (organizationId && typeof args === "object" && args.method !== "POST")
    {
      await cacheCollection(organizationId, args.url, result.data)
    }
    return result
  }
  const organizationId = api.getState().organization.selectedId
  if (organizationId && typeof args === "object" && args.method !== "POST")
  {
    const cached = await readCachedCollection(organizationId, args.url)
    if (cached !== undefined) return { data: cached, meta: { offline: true } }
  }
  return result
}

export const daymarkApi = createApi({
  reducerPath: "daymarkApi",
  baseQuery: offlineBaseQuery,
  tagTypes: ["Dashboard", "Product", "Customer", "Inventory", "Order", "Sync", "Billing", "Profile", "PlatformSettings"],
  endpoints: (build) => ({
    dashboard: build.query({ query: (organizationId) => `/api/organizations/${organizationId}/dashboard/`, providesTags: ["Dashboard"] }),
    products: build.query({ query: (organizationId) => `/api/organizations/${organizationId}/products/`, providesTags: ["Product"] }),
    createProduct: build.mutation({ query: ({ organizationId, ...body }) => ({ url: `/api/organizations/${organizationId}/products/`, method: "POST", body }), invalidatesTags: ["Product", "Inventory", "Dashboard"] }),
    updateProduct: build.mutation({ query: ({ organizationId, productId, ...body }) => ({ url: `/api/organizations/${organizationId}/products/${productId}`, method: "PATCH", body }), invalidatesTags: ["Product", "Inventory", "Dashboard"] }),
    customers: build.query({ query: (organizationId) => `/api/organizations/${organizationId}/customers/`, providesTags: ["Customer"] }),
    createCustomer: build.mutation({ query: ({ organizationId, ...body }) => ({ url: `/api/organizations/${organizationId}/customers/`, method: "POST", body }), invalidatesTags: ["Customer", "Dashboard", "Sync"] }),
    updateCustomer: build.mutation({ query: ({ organizationId, customerId, ...body }) => ({ url: `/api/organizations/${organizationId}/customers/${customerId}`, method: "PATCH", body }), invalidatesTags: ["Customer", "Dashboard", "Sync"] }),
    inventory: build.query({ query: (organizationId) => `/api/organizations/${organizationId}/inventory/movements`, providesTags: ["Inventory"] }),
    createInventoryMovement: build.mutation({ query: ({ organizationId, productId, ...body }) => ({ url: `/api/organizations/${organizationId}/products/${productId}/inventory/`, method: "POST", body }), invalidatesTags: ["Inventory", "Product", "Dashboard", "Sync"] }),
    orders: build.query({ query: (organizationId) => `/api/organizations/${organizationId}/orders/`, providesTags: ["Order"] }),
    createOrder: build.mutation({ query: ({ organizationId, ...body }) => ({ url: `/api/organizations/${organizationId}/orders/`, method: "POST", body }), invalidatesTags: ["Order", "Inventory", "Product", "Dashboard", "Sync"] }),
    completeOrder: build.mutation({ query: ({ organizationId, orderId }) => ({ url: `/api/organizations/${organizationId}/orders/${orderId}/complete`, method: "POST" }), invalidatesTags: ["Order", "Dashboard", "Inventory", "Product", "Sync"] }),
    cancelOrder: build.mutation({ query: ({ organizationId, orderId }) => ({ url: `/api/organizations/${organizationId}/orders/${orderId}/cancel`, method: "POST" }), invalidatesTags: ["Order", "Dashboard", "Inventory", "Product", "Sync"] }),
    activities: build.query({ query: (organizationId) => `/api/organizations/${organizationId}/activities/`, providesTags: ["Sync"] }),
    members: build.query({ query: (organizationId) => `/api/organizations/${organizationId}/members/`, providesTags: ["Sync"] }),
    updateMemberRole: build.mutation({ query: ({ organizationId, userId, role }) => ({ url: `/api/organizations/${organizationId}/members/${userId}`, method: "PATCH", body: { role } }), invalidatesTags: ["Sync"] }),
    removeMember: build.mutation({ query: ({ organizationId, userId }) => ({ url: `/api/organizations/${organizationId}/members/${userId}`, method: "DELETE" }), invalidatesTags: ["Sync"] }),
    invitations: build.query({ query: (organizationId) => `/api/organizations/${organizationId}/invitations/`, providesTags: ["Sync"] }),
    createInvitation: build.mutation({ query: ({ organizationId, ...body }) => ({ url: `/api/organizations/${organizationId}/invitations/`, method: "POST", body }), invalidatesTags: ["Sync"] }),
    resendInvitation: build.mutation({ query: ({ organizationId, invitationId }) => ({ url: `/api/organizations/${organizationId}/invitations/${invitationId}/resend`, method: "POST" }), invalidatesTags: ["Sync"] }),
    revokeInvitation: build.mutation({ query: ({ organizationId, invitationId }) => ({ url: `/api/organizations/${organizationId}/invitations/${invitationId}`, method: "DELETE" }), invalidatesTags: ["Sync"] }),
    syncStatus: build.query({ query: (organizationId) => `/api/organizations/${organizationId}/sync/status`, providesTags: ["Sync"] }),
    syncChanges: build.query({ query: ({ organizationId, since }) => ({ url: `/api/organizations/${organizationId}/sync/changes`, params: since ? { since } : undefined }), providesTags: ["Sync"] }),
    plans: build.query({ query: () => "/api/billing/plans", providesTags: ["Billing"] }),
    updatePlan: build.mutation({ query: ({ plan_key, ...body }) => ({ url: `/api/admin/plans/${plan_key}`, method: "PATCH", body }), invalidatesTags: ["Billing"] }),
    createPlan: build.mutation({ query: (body) => ({ url: "/api/admin/plans", method: "POST", body }), invalidatesTags: ["Billing"] }),
    platformSettings: build.query({ query: () => "/api/admin/settings", providesTags: ["PlatformSettings"] }),
    publicPlatformSettings: build.query({ query: () => "/api/admin/public/settings" }),
    updatePlatformSettings: build.mutation({ query: (body) => ({ url: "/api/admin/settings", method: "PUT", body }), invalidatesTags: ["PlatformSettings"] }),
    announcements: build.query({ query: ({ activeOnly = false } = {}) => ({ url: "/api/admin/announcements", params: { active_only: activeOnly } }) }),
    publicAnnouncements: build.query({ query: ({ activeOnly = false } = {}) => ({ url: "/api/admin/public/announcements", params: { active_only: activeOnly } }) }),
    createAnnouncement: build.mutation({ query: (body) => ({ url: "/api/admin/announcements", method: "POST", body }) }),
    emailPreview: build.mutation({ query: (body) => ({ url: "/api/admin/email/preview", method: "POST", body }) }),
    emailSend: build.mutation({ query: (body) => ({ url: "/api/admin/email/send", method: "POST", body }) }),
    emailMetrics: build.query({ query: () => "/api/admin/email/metrics" }),
    emailHistory: build.query({ query: ({ page = 1, limit = 25 } = {}) => ({ url: "/api/admin/email/history", params: { page, limit } }) }),
    auditLogs: build.query({ query: ({ page = 1, limit = 20 } = {}) => ({ url: "/api/admin/audit-logs", params: { page, limit } }) }),
    analytics: build.query({ query: () => "/api/admin/analytics" }),
    platformHealth: build.query({ query: () => "/api/admin/health" }),
    billing: build.query({ query: (organizationId) => `/api/organizations/${organizationId}/billing`, providesTags: ["Billing"] }),
    billingHistory: build.query({ query: (organizationId) => `/api/organizations/${organizationId}/billing/history`, providesTags: ["Billing"] }),
    initializeCheckout: build.mutation({ query: ({ organizationId, ...body }) => ({ url: `/api/organizations/${organizationId}/billing/checkout`, method: "POST", body }), invalidatesTags: ["Billing"] }),
    verifyPayment: build.mutation({ query: ({ organizationId, reference }) => ({ url: `/api/organizations/${organizationId}/billing/verify`, method: "POST", body: { reference } }), invalidatesTags: ["Billing"] }),
    cancelSubscription: build.mutation({ query: (organizationId) => ({ url: `/api/organizations/${organizationId}/billing/cancel`, method: "POST" }), invalidatesTags: ["Billing"] }),
    adminDashboard: build.query({ query: () => "/api/admin/dashboard" }),
    login: build.mutation({ query: (body) => ({ url: "/api/auth/login", method: "POST", body }) }),
    register: build.mutation({ query: (body) => ({ url: "/api/auth/register", method: "POST", body }) }),
    registerInvitation: build.mutation({ query: (body) => ({ url: "/api/invitations/register", method: "POST", body }) }),
    acceptInvitation: build.mutation({ query: (body) => ({ url: "/api/invitations/accept", method: "POST", body }) }),
    verifyEmail: build.mutation({ query: (body) => ({ url: "/api/auth/verify-email", method: "POST", body }) }),
    resendVerification: build.mutation({ query: (body) => ({ url: "/api/auth/resend-verification", method: "POST", body }) }),
    me: build.query({ query: () => "/api/auth/me", providesTags: ["Profile"] }),
    updateMe: build.mutation({ query: (body) => ({ url: "/api/auth/me", method: "PATCH", body }), invalidatesTags: ["Profile"] }),
    organizations: build.query({ query: () => "/api/organizations/" }),
    organization: build.query({ query: (organizationId) => `/api/organizations/${organizationId}`, providesTags: ["Profile"] }),
    createOrganization: build.mutation({ query: (body) => ({ url: "/api/organizations/", method: "POST", params: typeof body === "string" ? { name: body } : body }) }),
    updateOrganization: build.mutation({ query: ({ organizationId, ...body }) => ({ url: `/api/organizations/${organizationId}`, method: "PATCH", body }), invalidatesTags: ["Profile", "Sync"] }),
    leaveOrganization: build.mutation({ query: (organizationId) => ({ url: `/api/organizations/${organizationId}/leave`, method: "DELETE" }), invalidatesTags: ["Sync"] }),
  }),
})

export const { useDashboardQuery, useProductsQuery, useCreateProductMutation, useUpdateProductMutation, useCreateInventoryMovementMutation, useCreateCustomerMutation, useUpdateCustomerMutation, useCustomersQuery, useCreateOrderMutation, useCompleteOrderMutation, useCancelOrderMutation, useInventoryQuery, useOrdersQuery, useActivitiesQuery, useMembersQuery, useUpdateMemberRoleMutation, useRemoveMemberMutation, useInvitationsQuery, useCreateInvitationMutation, useResendInvitationMutation, useRevokeInvitationMutation, useAcceptInvitationMutation, useSyncStatusQuery, useSyncChangesQuery, usePlansQuery, useUpdatePlanMutation, usePlatformSettingsQuery, usePublicPlatformSettingsQuery, useUpdatePlatformSettingsMutation, useAnnouncementsQuery, usePublicAnnouncementsQuery, useCreateAnnouncementMutation, useEmailPreviewMutation, useEmailSendMutation, useEmailMetricsQuery, useEmailHistoryQuery, useAuditLogsQuery, useAnalyticsQuery, usePlatformHealthQuery, useBillingQuery, useBillingHistoryQuery, useInitializeCheckoutMutation, useVerifyPaymentMutation, useCancelSubscriptionMutation, useAdminDashboardQuery, useLoginMutation, useRegisterMutation, useRegisterInvitationMutation, useVerifyEmailMutation, useResendVerificationMutation, useMeQuery, useUpdateMeMutation, useOrganizationsQuery, useOrganizationQuery, useCreateOrganizationMutation, useUpdateOrganizationMutation, useLeaveOrganizationMutation } = daymarkApi
export const useCreatePlanMutation = daymarkApi.useCreatePlanMutation

import { createBrowserRouter } from "react-router";
import { PublicLayout, AuthLayout } from "../components/Layout";
import { Home } from "../pages/Home";
import { Features, Solutions, About, Contact } from "../pages/PublicPages";
import {
  Login,
  Register,
  InvitationRegister,
  ForgotPassword,
  ResetPassword,
} from "../pages/AuthPages";
import { Privacy, Terms } from "../pages/LegalPages";
import { Pricing } from "../pages/Pricing";
import { VerifyEmail, VerificationSent } from "../pages/EmailVerification";
import { AppLayout, Organizations } from "../features/app/layout/AppLayout";
import { Dashboard } from "../features/app/pages/DashboardPage";
import { Products, ProductForm } from "../features/app/pages/ProductsPages";
import {
  ProductDetails,
  Inventory,
  Customers,
  CustomerForm,
  CustomerDetails,
  Orders,
  CreateOrder,
  OrderDetails,
} from "../features/app/pages/CommercePages";
import {
  Activity,
  Team,
  Invitations,
  Settings,
  Profile,
  SyncCentre,
} from "../features/app/pages/ManagementPages";
import { Billing } from "../features/app/pages/BillingPage";
import { PaymentReturn } from "../features/app/pages/PaymentReturnPage";
import { AdminLayout } from "../features/admin/AdminLayout";
import { AdminOverview } from "../features/admin/pages/OverviewPage";
import {
  Businesses,
  Users,
  Subscriptions,
  Payments,
  Plans,
} from "../features/admin/pages/BusinessAdminPages";
import {
  EmailCentreOverview,
  EmailCompose,
  EmailTemplates,
  EmailAutomation,
  EmailHistory,
} from "../features/admin/pages/CommunicationPages";
import {
  Analytics,
  PlatformSettings,
  SystemHealth,
  SupportTickets,
  FeedbackBoard,
  Promotions,
} from "../features/admin/pages/OperationsPages";
import {
  Announcements,
  AuditLogs,
  FeatureFlags as GovernanceFeatureFlags,
  SecurityAccess as GovernanceSecurityAccess,
  Backups as GovernanceBackups,
} from "../features/admin/pages/GovernancePages";
import { NotFoundPage, RouteErrorPage } from "../components/ErrorBoundary";

export const router = createBrowserRouter([
  {
    Component: PublicLayout,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, Component: Home },
      { path: "features", Component: Features },
      { path: "solutions", Component: Solutions },
      { path: "about", Component: About },
      { path: "contact", Component: Contact },
      { path: "privacy", Component: Privacy },
      { path: "terms", Component: Terms },
      { path: "pricing", Component: Pricing },
    ],
  },
  {
    Component: AuthLayout,
    errorElement: <RouteErrorPage />,
    children: [
      { path: "login", Component: Login },
      { path: "register", Component: Register },
      { path: "invitations/accept", Component: InvitationRegister },
      { path: "forgot-password", Component: ForgotPassword },
      { path: "reset-password", Component: ResetPassword },
      { path: "verify-email", Component: VerifyEmail },
      { path: "verify-email/sent", Component: VerificationSent },
    ],
  },
  {
    path: "admin",
    Component: AdminLayout,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, Component: AdminOverview },
      { path: "businesses", Component: Businesses },
      { path: "users", Component: Users },
      { path: "subscriptions", Component: Subscriptions },
      { path: "payments", Component: Payments },
      { path: "plans", Component: Plans },
      { path: "email-centre", Component: EmailCentreOverview },
      { path: "email-centre/compose", Component: EmailCompose },
      { path: "email-centre/templates", Component: EmailTemplates },
      { path: "email-centre/automation", Component: EmailAutomation },
      { path: "email-centre/history", Component: EmailHistory },
      { path: "analytics", Component: Analytics },
      { path: "health", Component: SystemHealth },
      { path: "support", Component: SupportTickets },
      { path: "feedback", Component: FeedbackBoard },
      { path: "promotions", Component: Promotions },
      { path: "announcements", Component: Announcements },
      { path: "feature-flags", Component: GovernanceFeatureFlags },
      { path: "security", Component: GovernanceSecurityAccess },
      { path: "backups", Component: GovernanceBackups },
      { path: "settings", Component: PlatformSettings },
      { path: "audit-logs", Component: AuditLogs },
    ],
  },
  { path: "app/organizations", Component: Organizations },
  {
    path: "app/:organizationId",
    Component: AppLayout,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, Component: Dashboard },
      { path: "dashboard", Component: Dashboard },
      { path: "products", Component: Products },
      { path: "products/new", Component: ProductForm },
      { path: "products/:productId/edit", Component: ProductForm },
      { path: "products/:productId", Component: ProductDetails },
      { path: "inventory", Component: Inventory },
      { path: "customers", Component: Customers },
      { path: "customers/new", Component: CustomerForm },
      { path: "customers/:customerId/edit", Component: CustomerForm },
      { path: "customers/:customerId", Component: CustomerDetails },
      { path: "orders", Component: Orders },
      { path: "orders/new", Component: CreateOrder },
      { path: "orders/:orderId", Component: OrderDetails },
      { path: "activity", Component: Activity },
      { path: "team", Component: Team },
      { path: "invitations", Component: Invitations },
      { path: "settings", Component: Settings },
      { path: "profile", Component: Profile },
      { path: "sync", Component: SyncCentre },
      { path: "billing", Component: Billing },
      { path: "settings/billing", Component: Billing },
      { path: "settings/billing/payment-return", Component: PaymentReturn },
    ],
  },
  { path: "*", Component: NotFoundPage },
]);

function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center bg-ink px-6 text-paper">
      <div className="max-w-lg text-center">
        <span className="eyebrow text-sage">404 / NOT FOUND</span>
        <h1 className="mt-6 text-5xl">This page isn’t on the day’s agenda.</h1>
        <a className="button button-light mt-8" href="/">
          Return home
        </a>
      </div>
    </main>
  );
}

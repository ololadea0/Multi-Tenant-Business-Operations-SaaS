import { RouterProvider } from "react-router"
import { router } from "./app/routes"
import { ReactErrorBoundary } from "./components/ErrorBoundary"

export default function App() {
  return <ReactErrorBoundary><RouterProvider router={router} /></ReactErrorBoundary>
}

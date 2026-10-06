import { RouterProvider } from 'react-router-dom'
import { AuthProvider } from '@/features/auth/auth-context'
import { ToastProvider } from '@/features/feedback/toast-context'
import { ErrorBoundary } from '@/components/error-boundary'
import { router } from '@/routes/router'

export function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </ToastProvider>
    </ErrorBoundary>
  )
}

import { RouterProvider } from 'react-router-dom'
import { AuthProvider } from '@/features/auth/auth-context'
import { ToastProvider } from '@/features/feedback/toast-context'
import { ErrorBoundary } from '@/components/error-boundary'
import { router } from '@/routes/router'
import { AuthLanguageSync, I18nProvider } from '@/i18n/provider'

export function App() {
  return (
    <I18nProvider>
      <ErrorBoundary>
        <ToastProvider>
          <AuthProvider>
            <AuthLanguageSync />
            <RouterProvider router={router} />
          </AuthProvider>
        </ToastProvider>
      </ErrorBoundary>
    </I18nProvider>
  )
}

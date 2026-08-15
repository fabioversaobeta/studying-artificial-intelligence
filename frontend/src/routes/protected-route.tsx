import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/hooks/use-auth'
import { PageSpinner } from '@/components/ui/spinner'

export function ProtectedRoute() {
  const { user, isLoading } = useAuth()

  if (isLoading) return <PageSpinner />
  if (!user) return <Navigate to="/login" replace />

  return <Outlet />
}

export function GuestOnlyRoute() {
  const { user, isLoading } = useAuth()

  if (isLoading) return <PageSpinner />
  if (user) return <Navigate to="/" replace />

  return <Outlet />
}

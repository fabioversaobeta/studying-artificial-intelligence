import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { GuestOnlyRoute, ProtectedRoute } from '@/routes/protected-route'
import { useAuth } from '@/hooks/use-auth'

vi.mock('@/hooks/use-auth', () => ({ useAuth: vi.fn() }))
vi.mock('@/components/ui/spinner', () => ({
  PageSpinner: () => <div>loading-spinner</div>,
}))

const useAuthMock = vi.mocked(useAuth)

function setAuth(state: { user: object | null; isLoading: boolean }) {
  useAuthMock.mockReturnValue(state as unknown as ReturnType<typeof useAuth>)
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<div>private-home</div>} />
        </Route>
        <Route element={<GuestOnlyRoute />}>
          <Route path="/login" element={<div>login-page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  useAuthMock.mockReset()
})

describe('ProtectedRoute', () => {
  it('shows a spinner while auth is loading', () => {
    setAuth({ user: null, isLoading: true })
    renderAt('/')
    expect(screen.getByText('loading-spinner')).toBeInTheDocument()
  })

  it('redirects to /login when unauthenticated', () => {
    setAuth({ user: null, isLoading: false })
    renderAt('/')
    expect(screen.getByText('login-page')).toBeInTheDocument()
    expect(screen.queryByText('private-home')).not.toBeInTheDocument()
  })

  it('renders the protected content when authenticated', () => {
    setAuth({ user: { id: '1' }, isLoading: false })
    renderAt('/')
    expect(screen.getByText('private-home')).toBeInTheDocument()
  })
})

describe('GuestOnlyRoute', () => {
  it('redirects authenticated users to /', () => {
    setAuth({ user: { id: '1' }, isLoading: false })
    renderAt('/login')
    expect(screen.getByText('private-home')).toBeInTheDocument()
  })

  it('renders the guest content when unauthenticated', () => {
    setAuth({ user: null, isLoading: false })
    renderAt('/login')
    expect(screen.getByText('login-page')).toBeInTheDocument()
  })
})

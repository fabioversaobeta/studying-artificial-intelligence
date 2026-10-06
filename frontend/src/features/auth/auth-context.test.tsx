import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '@/features/auth/auth-context'
import { useAuth } from '@/hooks/use-auth'
import { session } from '@/lib/session'
import { apiError, mockFetch } from '@/test/fetch-mock'

const user = { id: 'u1', email: 'a@b.com', display_name: 'Ada', is_active: true }
const tokens = { access_token: 'acc', token_type: 'bearer' }

function Probe() {
  const { user: u, isLoading, login, logout } = useAuth()
  return (
    <div>
      <p>{isLoading ? 'loading' : 'ready'}</p>
      <p>{u ? `user:${u.display_name}` : 'anonymous'}</p>
      <button onClick={() => void login('a@b.com', 'pw').catch(() => undefined)}>do-login</button>
      <button onClick={logout}>do-logout</button>
    </div>
  )
}

function renderProbe() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  )
}

beforeEach(() => localStorage.clear())
afterEach(() => vi.unstubAllGlobals())

function calls(fetchMock: ReturnType<typeof mockFetch>, suffix: string) {
  return fetchMock.mock.calls.filter(([url]) => String(url).endsWith(suffix))
}

describe('AuthProvider', () => {
  it('finishes loading as anonymous when there is no session cookie', async () => {
    const fetchMock = mockFetch({}) // the restore attempt gets 401 by default
    renderProbe()
    expect(await screen.findByText('anonymous')).toBeInTheDocument()
    expect(screen.getByText('ready')).toBeInTheDocument()
    expect(calls(fetchMock, '/auth/refresh')).toHaveLength(1)
    expect(calls(fetchMock, '/auth/me')).toHaveLength(0)
  })

  it('restores the session on load from the refresh cookie (memory-only access token)', async () => {
    mockFetch({
      'POST /api/v1/auth/refresh': { body: tokens },
      'GET /api/v1/auth/me': { body: user },
    })
    renderProbe()
    expect(screen.getByText('loading')).toBeInTheDocument()
    expect(await screen.findByText('user:Ada')).toBeInTheDocument()
    expect(session.getAccessToken()).toBe('acc')
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
  })

  it('uses an access token already in memory without refreshing', async () => {
    session.setAccessToken('acc')
    const fetchMock = mockFetch({ 'GET /api/v1/auth/me': { body: user } })
    renderProbe()
    expect(await screen.findByText('user:Ada')).toBeInTheDocument()
    expect(calls(fetchMock, '/auth/refresh')).toHaveLength(0)
  })

  it('falls back to anonymous when the restored session is invalid', async () => {
    mockFetch({
      'POST /api/v1/auth/refresh': { body: tokens },
      'GET /api/v1/auth/me': apiError(401, 'authentication_error', 'nope'),
    })
    renderProbe()
    expect(await screen.findByText('anonymous')).toBeInTheDocument()
  })

  it('logs in: keeps the access token in memory only and loads the user', async () => {
    mockFetch({
      'POST /api/v1/auth/login': { body: tokens },
      'GET /api/v1/auth/me': { body: user },
    })
    renderProbe()
    await screen.findByText('anonymous')
    await userEvent.click(screen.getByText('do-login'))
    expect(await screen.findByText('user:Ada')).toBeInTheDocument()
    expect(session.getAccessToken()).toBe('acc')
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
  })

  it('stays anonymous when login fails', async () => {
    mockFetch({ 'POST /api/v1/auth/login': apiError(401, 'authentication_error', 'Bad creds') })
    renderProbe()
    await screen.findByText('anonymous')
    await userEvent.click(screen.getByText('do-login'))
    await waitFor(() => expect(screen.getByText('anonymous')).toBeInTheDocument())
    expect(session.getAccessToken()).toBeNull()
  })

  it('logs out: clears the token and user, and revokes the cookie server-side', async () => {
    session.setAccessToken('acc')
    const fetchMock = mockFetch({
      'GET /api/v1/auth/me': { body: user },
      'POST /api/v1/auth/logout': { status: 204 },
    })
    renderProbe()
    await screen.findByText('user:Ada')
    await userEvent.click(screen.getByText('do-logout'))
    expect(screen.getByText('anonymous')).toBeInTheDocument()
    expect(session.getAccessToken()).toBeNull()
    await waitFor(() => {
      const [call] = calls(fetchMock, '/auth/logout')
      expect(call).toBeDefined()
      const init = call[1] as RequestInit
      expect(init.body).toBeUndefined() // the refresh token is in the cookie, not the body
      expect(init.credentials).toBe('include')
      const headers = init.headers as Record<string, string>
      expect(headers['Authorization']).toBe('Bearer acc')
      expect(headers['X-CSRF-Protection']).toBe('1')
    })
  })

  it('still logs out locally when the revoke call fails', async () => {
    session.setAccessToken('acc')
    mockFetch({
      'GET /api/v1/auth/me': { body: user },
      'POST /api/v1/auth/logout': apiError(500, 'internal_error', 'boom'),
    })
    renderProbe()
    await screen.findByText('user:Ada')
    await userEvent.click(screen.getByText('do-logout'))
    expect(screen.getByText('anonymous')).toBeInTheDocument()
    expect(session.getAccessToken()).toBeNull()
  })

  it('useAuth throws outside a provider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    expect(() => render(<Probe />)).toThrow(/AuthProvider/)
    spy.mockRestore()
  })
})

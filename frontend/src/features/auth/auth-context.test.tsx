import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '@/features/auth/auth-context'
import { useAuth } from '@/hooks/use-auth'
import { tokenStorage } from '@/lib/token-storage'
import { apiError, mockFetch } from '@/test/fetch-mock'

const user = { id: 'u1', email: 'a@b.com', display_name: 'Ada', is_active: true }
const tokens = { access_token: 'acc', refresh_token: 'ref', token_type: 'bearer' }

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

describe('AuthProvider', () => {
  it('finishes loading as anonymous without a stored token, without calling the API', async () => {
    const fetchMock = mockFetch({})
    renderProbe()
    expect(await screen.findByText('anonymous')).toBeInTheDocument()
    expect(screen.getByText('ready')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('restores the session from a stored token', async () => {
    tokenStorage.setTokens('acc', 'ref')
    mockFetch({ 'GET /api/v1/auth/me': { body: user } })
    renderProbe()
    expect(screen.getByText('loading')).toBeInTheDocument()
    expect(await screen.findByText('user:Ada')).toBeInTheDocument()
  })

  it('falls back to anonymous when the stored session is invalid', async () => {
    tokenStorage.setTokens('bad', 'bad')
    mockFetch({
      'GET /api/v1/auth/me': apiError(401, 'authentication_error', 'nope'),
      'POST /api/v1/auth/refresh': apiError(401, 'authentication_error', 'expired'),
    })
    renderProbe()
    expect(await screen.findByText('anonymous')).toBeInTheDocument()
    expect(tokenStorage.getAccessToken()).toBeNull()
  })

  it('logs in: stores tokens and loads the user', async () => {
    mockFetch({
      'POST /api/v1/auth/login': { body: tokens },
      'GET /api/v1/auth/me': { body: user },
    })
    renderProbe()
    await screen.findByText('anonymous')
    await userEvent.click(screen.getByText('do-login'))
    expect(await screen.findByText('user:Ada')).toBeInTheDocument()
    expect(tokenStorage.getAccessToken()).toBe('acc')
    expect(tokenStorage.getRefreshToken()).toBe('ref')
  })

  it('stays anonymous when login fails', async () => {
    mockFetch({ 'POST /api/v1/auth/login': apiError(401, 'authentication_error', 'Bad creds') })
    renderProbe()
    await screen.findByText('anonymous')
    await userEvent.click(screen.getByText('do-login'))
    await waitFor(() => expect(screen.getByText('anonymous')).toBeInTheDocument())
    expect(tokenStorage.getAccessToken()).toBeNull()
  })

  it('logs out: clears tokens and user', async () => {
    tokenStorage.setTokens('acc', 'ref')
    mockFetch({ 'GET /api/v1/auth/me': { body: user } })
    renderProbe()
    await screen.findByText('user:Ada')
    await userEvent.click(screen.getByText('do-logout'))
    expect(screen.getByText('anonymous')).toBeInTheDocument()
    expect(tokenStorage.getAccessToken()).toBeNull()
  })

  it('useAuth throws outside a provider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    expect(() => render(<Probe />)).toThrow(/AuthProvider/)
    spy.mockRestore()
  })
})

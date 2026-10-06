import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '@/features/auth/auth-context'
import { LoginPage } from '@/pages/login-page'
import { apiError, mockFetch } from '@/test/fetch-mock'

const user = { id: 'u1', email: 'a@b.com', display_name: 'Ada', is_active: true }
const tokens = { access_token: 'acc', refresh_token: 'ref', token_type: 'bearer' }

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<div>register-screen</div>} />
          <Route path="/" element={<div>home-screen</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

async function fillAndSubmit() {
  await userEvent.type(screen.getByLabelText('Email'), 'a@b.com')
  await userEvent.type(screen.getByLabelText('Password'), 'secret123')
  await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
}

beforeEach(() => localStorage.clear())
afterEach(() => vi.unstubAllGlobals())

describe('LoginPage', () => {
  it('renders fields and a link to register', async () => {
    mockFetch({})
    renderPage()
    expect(screen.getByLabelText('Email')).toHaveAttribute('type', 'email')
    expect(screen.getByLabelText('Password')).toBeRequired()
    await userEvent.click(screen.getByRole('link', { name: 'Register' }))
    expect(screen.getByText('register-screen')).toBeInTheDocument()
  })

  it('submits credentials and redirects home on success', async () => {
    const fetchMock = mockFetch({
      'POST /api/v1/auth/login': { body: tokens },
      'GET /api/v1/auth/me': { body: user },
    })
    renderPage()
    await fillAndSubmit()
    expect(await screen.findByText('home-screen')).toBeInTheDocument()
    const loginCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith('/auth/login'))!
    expect(JSON.parse(String(loginCall[1]?.body))).toEqual({
      email: 'a@b.com',
      password: 'secret123',
    })
  })

  it('shows the API error message and stays on the page', async () => {
    mockFetch({
      'POST /api/v1/auth/login': apiError(401, 'authentication_error', 'Invalid email or password'),
    })
    renderPage()
    await fillAndSubmit()
    expect(await screen.findByText('Invalid email or password')).toBeInTheDocument()
    expect(screen.queryByText('home-screen')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Log in' })).toBeEnabled()
  })

  it('shows a generic message on network failure', async () => {
    mockFetch({}) // unmocked request rejects like a network error
    renderPage()
    await fillAndSubmit()
    expect(await screen.findByText('Unable to log in')).toBeInTheDocument()
  })

  it('disables the button while submitting', async () => {
    let release!: () => void
    const gate = new Promise<void>((r) => (release = r))
    const fetchMock = mockFetch({ 'GET /api/v1/auth/me': { body: user } })
    fetchMock.mockImplementationOnce(async () => {
      await gate
      return new Response(JSON.stringify(tokens), { status: 200 })
    })
    renderPage()
    await fillAndSubmit()
    expect(screen.getByRole('button', { name: /Logging in/ })).toBeDisabled()
    release()
    expect(await screen.findByText('home-screen')).toBeInTheDocument()
  })

  it('does not call the API when required fields are empty', async () => {
    const fetchMock = mockFetch({})
    renderPage()
    await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
    expect(fetchMock).not.toHaveBeenCalled()
  })
})

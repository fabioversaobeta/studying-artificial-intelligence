import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '@/features/auth/auth-context'
import { RegisterPage } from '@/pages/register-page'
import { apiError, mockFetch } from '@/test/fetch-mock'

const user = { id: 'u1', email: 'a@b.com', display_name: 'Ada', is_active: true }
const tokens = { access_token: 'acc', refresh_token: 'ref', token_type: 'bearer' }

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/register']}>
      <AuthProvider>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/login" element={<div>login-screen</div>} />
          <Route path="/" element={<div>home-screen</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

async function fill(password = 'secret123') {
  await userEvent.type(screen.getByLabelText('Name'), 'Ada')
  await userEvent.type(screen.getByLabelText('Email'), 'a@b.com')
  await userEvent.type(screen.getByLabelText('Password'), password)
}

const submit = () => userEvent.click(screen.getByRole('button', { name: /Create account/ }))

beforeEach(() => localStorage.clear())
afterEach(() => vi.unstubAllGlobals())

describe('RegisterPage', () => {
  it('links back to login', async () => {
    mockFetch({})
    renderPage()
    await userEvent.click(screen.getByRole('link', { name: 'Log in' }))
    expect(screen.getByText('login-screen')).toBeInTheDocument()
  })

  it('registers and redirects home on success', async () => {
    const fetchMock = mockFetch({
      'POST /api/v1/auth/register': { status: 201, body: tokens },
      'GET /api/v1/auth/me': { body: user },
    })
    renderPage()
    await fill()
    await submit()
    expect(await screen.findByText('home-screen')).toBeInTheDocument()
    const call = fetchMock.mock.calls.find(([url]) => String(url).endsWith('/auth/register'))!
    expect(JSON.parse(String(call[1]?.body))).toMatchObject({
      email: 'a@b.com',
      password: 'secret123',
      display_name: 'Ada',
    })
  })

  it('shows the API error for a duplicate email', async () => {
    mockFetch({
      'POST /api/v1/auth/register': apiError(409, 'conflict', 'Email already registered'),
    })
    renderPage()
    await fill()
    await submit()
    expect(await screen.findByText('Email already registered')).toBeInTheDocument()
    expect(screen.queryByText('home-screen')).not.toBeInTheDocument()
  })

  it('declares an 8-character minimum on the password field', () => {
    mockFetch({})
    renderPage()
    // jsdom does not enforce minLength on submit, so assert the constraint itself.
    expect(screen.getByLabelText('Password')).toHaveAttribute('minlength', '8')
    expect(screen.getByText('At least 8 characters.')).toBeInTheDocument()
  })

  it('does not call the API when required fields are empty', async () => {
    const fetchMock = mockFetch({})
    renderPage()
    await submit()
    expect(fetchMock).not.toHaveBeenCalled()
  })
})

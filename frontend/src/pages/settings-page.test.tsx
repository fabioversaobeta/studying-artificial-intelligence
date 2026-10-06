import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { SettingsPage } from '@/pages/settings-page'
import { ToastProvider } from '@/features/feedback/toast-context'
import { apiError, mockFetch } from '@/test/fetch-mock'

const user = {
  id: 'u1',
  email: 'a@b.com',
  display_name: 'Ada',
  preferred_language: 'en',
  is_active: true,
}

function renderPage() {
  return render(
    <ToastProvider>
      <SettingsPage />
    </ToastProvider>,
  )
}

afterEach(() => vi.unstubAllGlobals())

describe('SettingsPage', () => {
  it('loads the current preferences into the form', async () => {
    mockFetch({ 'GET /api/v1/auth/me': { body: { ...user, preferred_language: 'pt-BR' } } })
    renderPage()
    expect(await screen.findByDisplayValue('Ada')).toBe(screen.getByLabelText('Display name'))
    expect(screen.getByLabelText('Content language')).toHaveValue('pt-BR')
  })

  it('saves the chosen language through PATCH /users/me', async () => {
    const fetchMock = mockFetch({
      'GET /api/v1/auth/me': { body: user },
      'PATCH /api/v1/users/me': (init) => ({
        body: { ...user, ...(JSON.parse(String(init.body)) as object) },
      }),
    })
    renderPage()
    await screen.findByLabelText('Content language')
    await userEvent.selectOptions(screen.getByLabelText('Content language'), 'pt-BR')
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    expect(await screen.findByText('Settings saved')).toBeInTheDocument()
    const patch = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH')
    expect(JSON.parse(String(patch?.[1]?.body))).toEqual({
      display_name: 'Ada',
      preferred_language: 'pt-BR',
    })
  })

  it('shows the server error when saving fails', async () => {
    mockFetch({
      'GET /api/v1/auth/me': { body: user },
      'PATCH /api/v1/users/me': apiError(422, 'validation_error', 'Invalid language'),
    })
    renderPage()
    await screen.findByLabelText('Content language')
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid language')
  })

  it('shows an error when the profile cannot be loaded', async () => {
    mockFetch({ 'GET /api/v1/auth/me': apiError(500, 'internal_error', 'Boom') })
    renderPage()
    expect(await screen.findByText('Boom')).toBeInTheDocument()
  })
})

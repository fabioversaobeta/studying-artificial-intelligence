import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '@/features/auth/auth-context'
import { ToastProvider } from '@/features/feedback/toast-context'
import { AuthLanguageSync, I18nProvider } from '@/i18n/provider'
import { LoginPage } from '@/pages/login-page'
import { QuizzesPage } from '@/pages/quizzes-page'
import { SettingsPage } from '@/pages/settings-page'
import { SubjectsPage } from '@/pages/subjects-page'
import { assessmentService } from '@/services/assessment-service'
import { learningService } from '@/services/learning-service'
import { mockFetch } from '@/test/fetch-mock'
import { paged } from '@/test/paged'
import type { Language, SubjectWithProgress } from '@/types/api'

vi.mock('@/services/learning-service', () => ({
  learningService: { listSubjects: vi.fn() },
}))
vi.mock('@/services/assessment-service', () => ({
  assessmentService: { listAssessments: vi.fn() },
}))

const subject: SubjectWithProgress = {
  subject: {
    id: 's1',
    name: 'Python',
    slug: 'python',
    description: 'About Python',
    icon: null,
    color: null,
    sort_order: 0,
  },
  competency_count: 12,
  average_mastery: 42.4,
}

function renderIn(language: Language, ui: React.ReactElement) {
  localStorage.setItem('lp.language', language)
  return render(
    <I18nProvider>
      <MemoryRouter>
        <ToastProvider>{ui}</ToastProvider>
      </MemoryRouter>
    </I18nProvider>,
  )
}

beforeEach(() => {
  vi.mocked(learningService.listSubjects).mockResolvedValue([subject])
  vi.mocked(assessmentService.listAssessments).mockResolvedValue(paged([]))
})
afterEach(() => vi.unstubAllGlobals())

describe('pages render in the stored language', () => {
  it('login page (logged out)', async () => {
    mockFetch({})
    renderIn('en', (
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    ))
    expect(screen.getByRole('heading', { name: 'Log in' })).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('en')
  })

  it('login page in pt-BR', () => {
    mockFetch({})
    renderIn('pt-BR', (
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    ))
    expect(screen.getByRole('heading', { name: 'Entrar' })).toBeInTheDocument()
    expect(screen.getByLabelText('Senha')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Cadastre-se' })).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('pt-BR')
  })

  it('subjects page', async () => {
    renderIn('en', <SubjectsPage />)
    expect(await screen.findByText('12 competencies')).toBeInTheDocument()
    expect(screen.getByText('42% mastery')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Subjects' })).toBeInTheDocument()
  })

  it('subjects page in pt-BR', async () => {
    renderIn('pt-BR', <SubjectsPage />)
    expect(await screen.findByText('12 competências')).toBeInTheDocument()
    expect(screen.getByText('42% de domínio')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Assuntos' })).toBeInTheDocument()
  })

  it('quizzes page', async () => {
    renderIn('en', <QuizzesPage />)
    expect(await screen.findByText('No quizzes available yet.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'History & stats' })).toBeInTheDocument()
  })

  it('quizzes page in pt-BR', async () => {
    renderIn('pt-BR', <QuizzesPage />)
    expect(await screen.findByText('Ainda não há quizzes disponíveis.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Histórico e estatísticas' })).toBeInTheDocument()
  })

  it('falls back to English when the stored value is not a supported language', () => {
    localStorage.setItem('lp.language', 'fr')
    render(
      <I18nProvider>
        <MemoryRouter>
          <SubjectsPage />
        </MemoryRouter>
      </I18nProvider>,
    )
    expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('en')
  })
})

describe('language switching', () => {
  const baseUser = {
    id: 'u1',
    email: 'a@b.com',
    display_name: 'Ada',
    preferred_language: 'en',
    is_active: true,
  }

  function renderApp(me: object) {
    const fetchMock = mockFetch({
      'POST /api/v1/auth/refresh': { body: { access_token: 'acc', token_type: 'bearer' } },
      'GET /api/v1/auth/me': { body: me },
      'PATCH /api/v1/users/me': (init) => ({
        body: { ...me, ...(JSON.parse(String(init.body)) as object) },
      }),
    })
    render(
      <I18nProvider>
        <ToastProvider>
          <AuthProvider>
            <AuthLanguageSync />
            <SettingsPage />
          </AuthProvider>
        </ToastProvider>
      </I18nProvider>,
    )
    return fetchMock
  }

  it('changes the interface immediately after saving in Settings, without a reload', async () => {
    renderApp(baseUser)
    await userEvent.selectOptions(await screen.findByLabelText('Language'), 'pt-BR')
    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    expect(await screen.findByRole('heading', { name: 'Configurações' })).toBeInTheDocument()
    expect(screen.getByLabelText('Idioma')).toHaveValue('pt-BR')
    expect(screen.getByRole('button', { name: 'Salvar alterações' })).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('pt-BR')
    expect(localStorage.getItem('lp.language')).toBe('pt-BR')

    // ...and back again.
    await userEvent.selectOptions(screen.getByLabelText('Idioma'), 'en')
    await userEvent.click(screen.getByRole('button', { name: 'Salvar alterações' }))
    expect(await screen.findByRole('heading', { name: 'Settings' })).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('en')
  })

  it("adopts the signed-in user's preferred_language over the stored one", async () => {
    localStorage.setItem('lp.language', 'en')
    renderApp({ ...baseUser, preferred_language: 'pt-BR' })
    expect(await screen.findByRole('heading', { name: 'Configurações' })).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('pt-BR')
  })
})

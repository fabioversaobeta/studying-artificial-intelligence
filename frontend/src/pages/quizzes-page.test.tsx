import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QuizzesPage } from '@/pages/quizzes-page'
import { QuizHistoryPage } from '@/pages/quiz-history-page'
import { ToastProvider } from '@/features/feedback/toast-context'
import { assessmentService } from '@/services/assessment-service'
import { ApiError } from '@/services/api-client'
import { paged } from '@/test/paged'
import { makeAttempt } from '@/test/quiz-fixtures'
import type { Assessment, AttemptSummary, CompetencyAssessmentStats } from '@/types/api'

vi.mock('@/services/assessment-service', () => ({
  assessmentService: {
    listAssessments: vi.fn(),
    startAttempt: vi.fn(),
    listAttempts: vi.fn(),
    competencyStats: vi.fn(),
  },
}))

const svc = vi.mocked(assessmentService)

const assessment = (overrides: Partial<Assessment> = {}): Assessment => ({
  id: 'a1',
  code: 'type-hints-quiz',
  title: 'Type Hints Quiz',
  description: 'What annotations do.',
  kind: 'competency',
  competency_id: 'c1',
  competency_name: 'Type Hints & Static Typing',
  pass_threshold: 70,
  completion_bonus_xp: 25,
  question_count: 6,
  attempts_completed: 0,
  best_score_percent: null,
  passed: false,
  open_attempt_id: null,
  ...overrides,
})

function renderQuizzes() {
  return render(
    <ToastProvider>
      <MemoryRouter initialEntries={['/quizzes']}>
        <Routes>
          <Route path="/quizzes" element={<QuizzesPage />} />
          <Route path="/quizzes/history" element={<p>history page</p>} />
          <Route path="/quizzes/attempts/:attemptId" element={<p>attempt page</p>} />
        </Routes>
      </MemoryRouter>
    </ToastProvider>,
  )
}

beforeEach(() => vi.resetAllMocks())

describe('QuizzesPage', () => {
  it('lists quizzes with their rules', async () => {
    svc.listAssessments.mockResolvedValue(paged([assessment()]))
    renderQuizzes()
    expect(await screen.findByRole('heading', { name: 'Type Hints Quiz' })).toBeInTheDocument()
    expect(screen.getByText('Type Hints & Static Typing')).toBeInTheDocument()
    expect(screen.getByText(/6 questions · pass at 70% · 25 XP bonus/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start: Type Hints Quiz' })).toBeEnabled()
  })

  it('starts an attempt and opens it', async () => {
    svc.listAssessments.mockResolvedValue(paged([assessment()]))
    svc.startAttempt.mockResolvedValue(makeAttempt({ id: 'attempt-9' }))
    renderQuizzes()
    await userEvent.click(await screen.findByRole('button', { name: 'Start: Type Hints Quiz' }))
    expect(svc.startAttempt).toHaveBeenCalledWith('a1')
    expect(await screen.findByText('attempt page')).toBeInTheDocument()
  })

  it('offers Resume for an open attempt and Try again after finishing', async () => {
    svc.listAssessments.mockResolvedValue(
      paged([
        assessment({ id: 'a1', title: 'Open one', open_attempt_id: 'att-1' }),
        assessment({
          id: 'a2',
          title: 'Done one',
          attempts_completed: 2,
          best_score_percent: 83.33,
          passed: true,
        }),
        assessment({ id: 'a3', title: 'Failed one', attempts_completed: 1, best_score_percent: 20 }),
      ]),
    )
    renderQuizzes()
    expect(await screen.findByRole('button', { name: 'Resume: Open one' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Try again: Done one' })).toBeInTheDocument()
    expect(screen.getByText('Passed')).toBeInTheDocument()
    expect(screen.getByText(/best 83.33%/)).toBeInTheDocument()
    expect(screen.getByText('Not passed yet')).toBeInTheDocument()
  })

  it('disables start when the quiz has no questions', async () => {
    svc.listAssessments.mockResolvedValue(paged([assessment({ question_count: 0 })]))
    renderQuizzes()
    expect(await screen.findByRole('button', { name: 'Start: Type Hints Quiz' })).toBeDisabled()
  })

  it('shows a toast and stays when starting fails', async () => {
    svc.listAssessments.mockResolvedValue(paged([assessment()]))
    svc.startAttempt.mockRejectedValue(new ApiError('conflict', 'No active questions', 409))
    renderQuizzes()
    await userEvent.click(await screen.findByRole('button', { name: 'Start: Type Hints Quiz' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('No active questions')
    expect(screen.queryByText('attempt page')).not.toBeInTheDocument()
  })

  it('shows the empty state and the load error', async () => {
    svc.listAssessments.mockResolvedValueOnce(paged([]))
    const { unmount } = renderQuizzes()
    expect(await screen.findByText('No quizzes available yet.')).toBeInTheDocument()
    unmount()

    svc.listAssessments.mockRejectedValueOnce(new ApiError('internal_error', 'Boom', 500))
    renderQuizzes()
    expect(await screen.findByText('Boom')).toBeInTheDocument()
  })

  it('paginates with Load more', async () => {
    svc.listAssessments
      .mockResolvedValueOnce(paged([assessment({ id: 'a1', title: 'First' })], 2))
      .mockResolvedValueOnce(paged([assessment({ id: 'a2', title: 'Second' })], 2))
    renderQuizzes()
    await screen.findByText('First')
    expect(screen.getByText('Showing 1 of 2')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Load more' }))
    expect(await screen.findByText('Second')).toBeInTheDocument()
    expect(svc.listAssessments).toHaveBeenLastCalledWith({ limit: 20, offset: 1 })
  })
})

describe('QuizHistoryPage', () => {
  const attempt = (overrides: Partial<AttemptSummary> = {}): AttemptSummary => ({
    id: 'att-1',
    assessment_id: 'a1',
    assessment_title: 'Type Hints Quiz',
    status: 'completed',
    started_at: '2026-01-01T10:00:00Z',
    completed_at: '2026-01-01T10:05:00Z',
    total_questions: 6,
    correct_count: 5,
    score_percent: 83.33,
    passed: true,
    xp_awarded: 145,
    ...overrides,
  })
  const stats: CompetencyAssessmentStats = {
    competency_id: 'c1',
    competency_name: 'Type Hints & Static Typing',
    subject_name: 'Python',
    questions_total: 6,
    questions_answered: 6,
    questions_correct: 5,
    coverage_percent: 83.33,
    attempts_completed: 2,
    responses_graded: 12,
    responses_correct: 9,
    accuracy_percent: 75,
    xp_earned: 120,
  }

  function renderHistory() {
    return render(
      <MemoryRouter>
        <QuizHistoryPage />
      </MemoryRouter>,
    )
  }

  it('shows attempts (linking to their review) and per-competency stats', async () => {
    svc.listAttempts.mockResolvedValue(
      paged([attempt(), attempt({ id: 'att-2', status: 'in_progress', passed: null })]),
    )
    svc.competencyStats.mockResolvedValue(paged([stats]))
    renderHistory()

    const table = await screen.findByRole('table', { name: 'Quiz statistics per competency' })
    expect(table).toHaveTextContent('5/6 (83.33%)')
    expect(table).toHaveTextContent('75%')
    expect(table).toHaveTextContent('Python')

    const links = await screen.findAllByRole('link', { name: /Type Hints Quiz/ })
    expect(links[0]).toHaveAttribute('href', '/quizzes/attempts/att-1')
    expect(links[0]).toHaveTextContent('5/6 · 83.33%')
    expect(links[0]).toHaveTextContent('+145 XP')
    expect(links[1]).toHaveTextContent('In progress')
  })

  it('has a friendly empty state', async () => {
    svc.listAttempts.mockResolvedValue(paged([]))
    svc.competencyStats.mockResolvedValue(paged([]))
    renderHistory()
    expect(await screen.findByText(/No attempts yet/)).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows errors from the attempts list', async () => {
    svc.listAttempts.mockRejectedValue(new ApiError('internal_error', 'History failed', 500))
    svc.competencyStats.mockResolvedValue(paged([]))
    renderHistory()
    expect(await screen.findByText('History failed')).toBeInTheDocument()
  })
})

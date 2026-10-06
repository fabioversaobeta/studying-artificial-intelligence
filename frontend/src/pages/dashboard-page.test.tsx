import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { DashboardPage } from '@/pages/dashboard-page'
import { ApiError } from '@/services/api-client'
import { learningService } from '@/services/learning-service'
import type { Dashboard } from '@/types/api'

vi.mock('@/services/learning-service', () => ({
  learningService: { getDashboard: vi.fn() },
}))

const getDashboard = vi.mocked(learningService.getDashboard)

const base: Dashboard = {
  level: 3,
  total_xp: 1250,
  xp_to_next_level: 150,
  current_streak_days: 4,
  longest_streak_days: 9,
  active_goals: [],
  due_review_count: 7,
  weakest_competencies: [],
  recent_study_sessions: [],
}

function renderPage() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  getDashboard.mockReset()
})

describe('DashboardPage', () => {
  it('shows a spinner while loading', () => {
    getDashboard.mockReturnValue(new Promise(() => undefined))
    renderPage()
    expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument()
  })

  it('shows the API error message', async () => {
    getDashboard.mockRejectedValue(new ApiError('server_error', 'Dashboard unavailable', 500))
    renderPage()
    expect(await screen.findByText('Dashboard unavailable')).toBeInTheDocument()
  })

  it('shows a generic message for non-API errors', async () => {
    getDashboard.mockRejectedValue(new Error('boom'))
    renderPage()
    expect(await screen.findByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders stats and empty states', async () => {
    getDashboard.mockResolvedValue(base)
    renderPage()
    expect(await screen.findByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
    expect(screen.getByText('1250')).toBeInTheDocument()
    expect(screen.getByText('150 XP to next')).toBeInTheDocument()
    expect(screen.getByText('4d')).toBeInTheDocument()
    expect(screen.getByText('Best: 9d')).toBeInTheDocument()
    expect(screen.getByText('7')).toBeInTheDocument()
    expect(screen.getByText(/No active goals yet/)).toBeInTheDocument()
    expect(screen.getByText(/Nothing tracked yet/)).toBeInTheDocument()
    expect(screen.getByText('No study sessions logged yet.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Set one' })).toHaveAttribute('href', '/goals')
    expect(screen.getByRole('link', { name: 'Start studying' })).toHaveAttribute('href', '/subjects')
  })

  it('renders goals, weakest competencies and recent sessions', async () => {
    getDashboard.mockResolvedValue({
      ...base,
      active_goals: [
        {
          id: 'g1',
          title: 'Ship the platform',
          description: null,
          status: 'active',
          target_date: '2026-12-31',
          created_at: '2026-01-01T00:00:00Z',
        },
      ],
      weakest_competencies: [
        { competency_id: 'abcdef12-0000-0000-0000-000000000000', score: 25, updated_at: '' },
        { competency_id: '12345678-0000-0000-0000-000000000000', score: 90, updated_at: '' },
      ],
      recent_study_sessions: [
        {
          id: 's1',
          competency_id: null,
          subject_id: null,
          duration_minutes: 45,
          notes: 'Read chapter 3',
          occurred_at: '2026-10-01T12:00:00Z',
        },
        {
          id: 's2',
          competency_id: null,
          subject_id: null,
          duration_minutes: 20,
          notes: null,
          occurred_at: '2026-10-02T12:00:00Z',
        },
      ],
    })
    renderPage()
    expect(await screen.findByText('Ship the platform')).toBeInTheDocument()
    expect(screen.getByText('by 2026-12-31')).toBeInTheDocument()
    expect(screen.getByText('Competency abcdef12')).toBeInTheDocument()
    expect(screen.getByText('25%')).toBeInTheDocument()
    expect(screen.getByText('90%')).toBeInTheDocument()
    expect(screen.getByText('Read chapter 3')).toBeInTheDocument()
    expect(screen.getByText('Study session')).toBeInTheDocument()
    expect(screen.getByText(/45 min/)).toBeInTheDocument()
    expect(screen.queryByText(/No active goals yet/)).not.toBeInTheDocument()
  })
})

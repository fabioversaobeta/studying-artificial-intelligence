import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TodayRecommendationsCard } from '@/features/recommendations/today-recommendations-card'
import { recommendationHref } from '@/features/recommendations/recommendation-href'
import { ApiError } from '@/services/api-client'
import { recommendationService } from '@/services/recommendation-service'
import type { Recommendation } from '@/types/api'

vi.mock('@/services/recommendation-service', () => ({
  recommendationService: { getToday: vi.fn() },
}))

const getToday = vi.mocked(recommendationService.getToday)

function item(overrides: Partial<Recommendation> & { id: string }): Recommendation {
  const { id, ...rest } = overrides
  return {
    kind: 'continue_learning',
    competency: { id, name: `Comp ${id}`, subject_id: `subj-${id}`, subject_name: 'Python' },
    reason: `Reason ${id}`,
    score: 50,
    action: { type: 'competency', id, slug: null },
    ...rest,
  }
}

function renderCard() {
  return render(
    <MemoryRouter>
      <TodayRecommendationsCard />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  getToday.mockReset()
})

describe('TodayRecommendationsCard', () => {
  it('shows a spinner while loading', () => {
    getToday.mockReturnValue(new Promise(() => undefined))
    renderCard()
    expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument()
  })

  it('shows the error with a working retry', async () => {
    getToday.mockRejectedValueOnce(new ApiError('server_error', 'Nope', 500))
    getToday.mockResolvedValueOnce([item({ id: '1' })])
    renderCard()
    expect(await screen.findByRole('alert')).toHaveTextContent('Nope')
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByText(/Reason 1/)).toBeInTheDocument()
  })

  it('shows an empty state', async () => {
    getToday.mockResolvedValue([])
    renderCard()
    expect(await screen.findByText(/Nothing to recommend/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Browse subjects' })).toHaveAttribute(
      'href',
      '/subjects',
    )
  })

  it('lists suggestions semantically with reasons and links', async () => {
    getToday.mockResolvedValue([
      item({
        id: 'r',
        kind: 'review_due',
        action: { type: 'review', id: 'r', slug: null },
      }),
      item({ id: 'c' }),
      item({ id: 'q', kind: 'take_quiz', action: { type: 'assessment', id: 'a1', slug: null } }),
      item({ id: 'p', kind: 'next_in_path', action: { type: 'path', id: null, slug: 'my-path' } }),
    ])
    renderCard()
    expect(await screen.findByRole('region', { name: /Today's recommendations/ })).toBeVisible()
    expect(screen.getAllByRole('listitem')).toHaveLength(4)
    expect(screen.getByText(/Reason r/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Review now: Comp r' })).toHaveAttribute(
      'href',
      '/reviews',
    )
    expect(screen.getByRole('link', { name: 'Keep studying: Comp c' })).toHaveAttribute(
      'href',
      '/subjects/subj-c',
    )
    expect(screen.getByRole('link', { name: 'Take quiz: Comp q' })).toHaveAttribute(
      'href',
      '/quizzes',
    )
    expect(screen.getByRole('link', { name: 'Open path: Comp p' })).toHaveAttribute(
      'href',
      '/learning-paths/my-path',
    )
  })
})

describe('recommendationHref', () => {
  it('encodes the path slug', () => {
    expect(
      recommendationHref(
        item({ id: 'x', action: { type: 'path', id: null, slug: 'a b' } }),
      ),
    ).toBe('/learning-paths/a%20b')
  })
})

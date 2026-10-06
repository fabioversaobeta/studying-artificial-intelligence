import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ReviewsPage } from '@/pages/reviews-page'
import { learningService } from '@/services/learning-service'
import { paged } from '@/test/paged'
import { ApiError } from '@/services/api-client'
import type { Review } from '@/types/api'

vi.mock('@/services/learning-service', () => ({
  learningService: {
    listDueReviews: vi.fn(),
    submitRecall: vi.fn(),
    listSubjects: vi.fn(),
    getSubject: vi.fn(),
  },
}))

const svc = vi.mocked(learningService)

const review: Review = {
  id: 'r1',
  competency_id: 'c1',
  interval_days: 1,
  ease_factor: 2.5,
  repetitions: 0,
  due_at: '2026-01-01T00:00:00Z',
  last_reviewed_at: null,
  last_recall_quality: null,
}

function renderPage() {
  return render(
    <MemoryRouter>
      <ReviewsPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.resetAllMocks()
  svc.listSubjects.mockResolvedValue([])
})

describe('ReviewsPage', () => {
  it('shows the empty state when nothing is due', async () => {
    svc.listDueReviews.mockResolvedValue(paged([]))
    renderPage()
    expect(await screen.findByText(/Nothing to review right now/)).toBeInTheDocument()
  })

  it('shows an error when loading fails', async () => {
    svc.listDueReviews.mockRejectedValue(new ApiError('server_error', 'Boom', 500))
    renderPage()
    expect(await screen.findByText('Boom')).toBeInTheDocument()
  })

  it('submits a recall and shows the next interval', async () => {
    svc.listDueReviews.mockResolvedValue(paged([review]))
    svc.submitRecall.mockResolvedValue({ ...review, interval_days: 6, repetitions: 1 })
    renderPage()

    expect(await screen.findByText('1 review due')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '4 · Good' }))

    expect(svc.submitRecall).toHaveBeenCalledWith('c1', 4)
    expect(await screen.findByText(/Next review in 6 days/)).toBeInTheDocument()
    expect(screen.getByText('All caught up!')).toBeInTheDocument()
  })

  it('shows an inline error when submitting fails and keeps the buttons', async () => {
    svc.listDueReviews.mockResolvedValue(paged([review]))
    svc.submitRecall.mockRejectedValue(new ApiError('server_error', 'Nope', 500))
    renderPage()

    await userEvent.click(await screen.findByRole('button', { name: '2 · Almost' }))
    await waitFor(() => expect(screen.getByText('Nope')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: '2 · Almost' })).toBeEnabled()
  })

  it('loads more reviews with the next offset and hides the button at the end', async () => {
    const r2: Review = { ...review, id: 'r2', competency_id: 'c2' }
    svc.listDueReviews.mockResolvedValueOnce(paged([review], 2))
    svc.listDueReviews.mockResolvedValueOnce(paged([r2], 2))
    renderPage()

    expect(await screen.findByText('Showing 1 of 2')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Load more' }))

    expect(await screen.findByText('Showing 2 of 2')).toBeInTheDocument()
    expect(svc.listDueReviews).toHaveBeenLastCalledWith({ limit: 20, offset: 1 })
    expect(screen.queryByRole('button', { name: 'Load more' })).not.toBeInTheDocument()
  })
})

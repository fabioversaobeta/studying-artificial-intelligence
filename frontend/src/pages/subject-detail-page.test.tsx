import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { SubjectDetailPage } from '@/pages/subject-detail-page'
import { ApiError } from '@/services/api-client'
import { learningService } from '@/services/learning-service'
import type { CompetencyWithState, SubjectDetail } from '@/types/api'

vi.mock('@/services/learning-service', () => ({
  learningService: { getSubject: vi.fn() },
}))
// The card pulls in resources/challenges/session forms; those have their own
// concerns. Stub it so this test only covers the page.
vi.mock('@/features/learning/competency-card', () => ({
  CompetencyCard: ({ item, onActivity }: { item: CompetencyWithState; onActivity: () => void }) => (
    <div>
      <span>competency:{item.competency.name}</span>
      <button onClick={onActivity}>activity:{item.competency.name}</button>
    </div>
  ),
}))

const getSubject = vi.mocked(learningService.getSubject)

const detail = (names: string[]): SubjectDetail => ({
  subject: {
    id: 's1',
    name: 'Python',
    slug: 'python',
    description: 'All about Python',
    icon: null,
    color: null,
    sort_order: 0,
  },
  competencies: names.map((name, i) => ({
    competency: {
      id: `c${i}`,
      subject_id: 's1',
      name,
      slug: name,
      description: null,
      difficulty: 'beginner',
      sort_order: i,
    },
    mastery_score: 0,
    state: 'available',
  })),
})

function renderPage(path = '/subjects/s1') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/subjects/:id" element={<SubjectDetailPage />} />
        <Route path="/subjects" element={<div>subjects-screen</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  getSubject.mockReset()
})

describe('SubjectDetailPage', () => {
  it('shows a spinner while loading', () => {
    getSubject.mockReturnValue(new Promise(() => undefined))
    renderPage()
    expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument()
  })

  it('shows the API error message (e.g. unknown subject)', async () => {
    getSubject.mockRejectedValue(new ApiError('not_found', 'Subject not found', 404))
    renderPage('/subjects/missing')
    expect(await screen.findByText('Subject not found')).toBeInTheDocument()
    expect(getSubject).toHaveBeenCalledWith('missing')
  })

  it('renders the subject header and one card per competency', async () => {
    getSubject.mockResolvedValue(detail(['Variables', 'Loops']))
    renderPage()
    expect(await screen.findByRole('heading', { name: 'Python' })).toBeInTheDocument()
    expect(screen.getByText('All about Python')).toBeInTheDocument()
    expect(screen.getByText('competency:Variables')).toBeInTheDocument()
    expect(screen.getByText('competency:Loops')).toBeInTheDocument()
    expect(getSubject).toHaveBeenCalledWith('s1')
  })

  it('refetches the subject when a competency reports activity', async () => {
    getSubject.mockResolvedValue(detail(['Variables']))
    renderPage()
    await userEvent.click(await screen.findByText('activity:Variables'))
    expect(getSubject).toHaveBeenCalledTimes(2)
    // existing data stays on screen during the refetch (no spinner flash)
    expect(screen.getByText('competency:Variables')).toBeInTheDocument()
  })

  it('links back to the subject list', async () => {
    getSubject.mockResolvedValue(detail([]))
    renderPage()
    await userEvent.click(await screen.findByRole('link', { name: /All subjects/ }))
    expect(screen.getByText('subjects-screen')).toBeInTheDocument()
  })
})

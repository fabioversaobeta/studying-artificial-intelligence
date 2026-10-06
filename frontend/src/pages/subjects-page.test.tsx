import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { SubjectsPage } from '@/pages/subjects-page'
import { ApiError } from '@/services/api-client'
import { learningService } from '@/services/learning-service'
import type { SubjectWithProgress } from '@/types/api'

vi.mock('@/services/learning-service', () => ({
  learningService: { listSubjects: vi.fn() },
}))

const listSubjects = vi.mocked(learningService.listSubjects)

const item = (id: string, name: string, count: number, mastery: number): SubjectWithProgress => ({
  subject: {
    id,
    name,
    slug: name.toLowerCase(),
    description: `About ${name}`,
    icon: null,
    color: null,
    sort_order: 0,
  },
  competency_count: count,
  average_mastery: mastery,
})

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/subjects']}>
      <Routes>
        <Route path="/subjects" element={<SubjectsPage />} />
        <Route path="/subjects/:id" element={<div>detail-screen</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  listSubjects.mockReset()
})

describe('SubjectsPage', () => {
  it('shows a spinner while loading', () => {
    listSubjects.mockReturnValue(new Promise(() => undefined))
    renderPage()
    expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument()
  })

  it('shows the API error message', async () => {
    listSubjects.mockRejectedValue(new ApiError('server_error', 'Subjects unavailable', 500))
    renderPage()
    expect(await screen.findByText('Subjects unavailable')).toBeInTheDocument()
  })

  it('renders a card per subject with competency count and mastery', async () => {
    listSubjects.mockResolvedValue([item('s1', 'Python', 12, 42.4), item('s2', 'SQL', 3, 100)])
    renderPage()
    expect(await screen.findByRole('heading', { name: 'Python' })).toBeInTheDocument()
    expect(screen.getByText('About Python')).toBeInTheDocument()
    expect(screen.getByText('12 competencies')).toBeInTheDocument()
    expect(screen.getByText('42% mastery')).toBeInTheDocument()
    expect(screen.getByText('100% mastery')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /SQL/ })).toHaveAttribute('href', '/subjects/s2')
  })

  it('navigates to the subject detail when a card is clicked', async () => {
    listSubjects.mockResolvedValue([item('s1', 'Python', 1, 0)])
    renderPage()
    await userEvent.click(await screen.findByRole('link', { name: /Python/ }))
    expect(screen.getByText('detail-screen')).toBeInTheDocument()
  })

  it('renders no cards for an empty list', async () => {
    listSubjects.mockResolvedValue([])
    renderPage()
    expect(await screen.findByRole('heading', { name: 'Subjects' })).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})

import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { LearningPathDetailPage, LearningPathsPage } from '@/pages/learning-paths-page'
import { learningService } from '@/services/learning-service'
import { ApiError } from '@/services/api-client'
import type { LearningPath } from '@/types/api'

vi.mock('@/services/learning-service', () => ({
  learningService: { listLearningPaths: vi.fn(), getLearningPath: vi.fn() },
}))

const svc = vi.mocked(learningService)

const comp = (name: string) => ({
  id: name,
  subject_id: 'subj-1',
  name,
  slug: name,
  description: `${name} desc`,
  difficulty: 'beginner' as const,
  sort_order: 0,
})

const path: LearningPath = {
  id: 'p1',
  title: 'Backend basics',
  slug: 'backend-basics',
  description: 'Start here',
  items: [
    { competency: comp('Second'), sort_order: 2 },
    { competency: comp('First'), sort_order: 1 },
  ],
}

function renderAt(route: string) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/learning-paths" element={<LearningPathsPage />} />
        <Route path="/learning-paths/:slug" element={<LearningPathDetailPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => vi.resetAllMocks())

describe('LearningPathsPage', () => {
  it('lists paths linking to their detail page', async () => {
    svc.listLearningPaths.mockResolvedValue([path])
    renderAt('/learning-paths')
    const link = await screen.findByRole('link', { name: /Backend basics/ })
    expect(link).toHaveAttribute('href', '/learning-paths/backend-basics')
    expect(screen.getByText('2 steps')).toBeInTheDocument()
  })

  it('shows the empty state', async () => {
    svc.listLearningPaths.mockResolvedValue([])
    renderAt('/learning-paths')
    expect(await screen.findByText('No learning paths available yet.')).toBeInTheDocument()
  })

  it('shows an error', async () => {
    svc.listLearningPaths.mockRejectedValue(new ApiError('server_error', 'Boom', 500))
    renderAt('/learning-paths')
    expect(await screen.findByText('Boom')).toBeInTheDocument()
  })
})

describe('LearningPathDetailPage', () => {
  it('shows steps in order with links to the subject page', async () => {
    svc.getLearningPath.mockResolvedValue(path)
    renderAt('/learning-paths/backend-basics')
    expect(await screen.findByRole('heading', { name: 'Backend basics' })).toBeInTheDocument()
    expect(svc.getLearningPath).toHaveBeenCalledWith('backend-basics')
    const headings = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)
    expect(headings[0]).toContain('First')
    expect(headings[1]).toContain('Second')
    const links = screen.getAllByRole('link', { name: /Study in subject/ })
    expect(links[0]).toHaveAttribute('href', '/subjects/subj-1')
  })

  it('shows an error when the path is not found', async () => {
    svc.getLearningPath.mockRejectedValue(new ApiError('not_found', 'Path not found', 404))
    renderAt('/learning-paths/nope')
    expect(await screen.findByText('Path not found')).toBeInTheDocument()
  })
})

describe('learning path progress', () => {
  const progressPath: LearningPath = {
    ...path,
    items: [
      { competency: comp('First'), sort_order: 1, mastery_score: 90, state: 'mastered' },
      { competency: comp('Second'), sort_order: 2, mastery_score: 40, state: 'learning' },
    ],
    progress: { total_steps: 2, mastered_steps: 1, average_mastery: 65 },
  }

  it('shows per-step progress bars, state badges and an aggregate summary', async () => {
    svc.getLearningPath.mockResolvedValue(progressPath)
    renderAt('/learning-paths/backend-basics')

    expect(await screen.findByText(/1 of 2 steps mastered/)).toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: 'Path progress' })).toHaveAttribute(
      'aria-valuenow',
      '65',
    )
    expect(screen.getByRole('progressbar', { name: 'First mastery' })).toHaveAttribute(
      'aria-valuenow',
      '90',
    )
    expect(screen.getByRole('progressbar', { name: 'Second mastery' })).toHaveAttribute(
      'aria-valuenow',
      '40',
    )
    expect(screen.getByText('Mastered')).toBeInTheDocument()
    expect(screen.getByText('Learning')).toBeInTheDocument()
  })

  it('renders without progress UI when the API returns none', async () => {
    svc.getLearningPath.mockResolvedValue(path)
    renderAt('/learning-paths/backend-basics')

    expect(await screen.findByRole('heading', { name: 'Backend basics' })).toBeInTheDocument()
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
  })

  it('shows aggregate progress on the list', async () => {
    svc.listLearningPaths.mockResolvedValue([progressPath])
    renderAt('/learning-paths')

    expect(await screen.findByText(/2 steps · 1 mastered/)).toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: 'Backend basics progress' })).toHaveAttribute(
      'aria-valuenow',
      '65',
    )
  })
})

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { GoalsPage } from '@/pages/goals-page'
import { ApiError } from '@/services/api-client'
import { learningService } from '@/services/learning-service'
import type { LearningGoal } from '@/types/api'

vi.mock('@/services/learning-service', () => ({
  learningService: {
    listGoals: vi.fn(),
    createGoal: vi.fn(),
    updateGoalStatus: vi.fn(),
  },
}))

const listGoals = vi.mocked(learningService.listGoals)
const createGoal = vi.mocked(learningService.createGoal)
const updateGoalStatus = vi.mocked(learningService.updateGoalStatus)

const goal = (over: Partial<LearningGoal>): LearningGoal => ({
  id: 'g1',
  title: 'Learn Rust',
  description: null,
  status: 'active',
  target_date: null,
  created_at: '2026-01-01T00:00:00Z',
  ...over,
})

beforeEach(() => {
  listGoals.mockReset()
  createGoal.mockReset()
  updateGoalStatus.mockReset()
})

describe('GoalsPage', () => {
  it('shows a spinner while loading', () => {
    listGoals.mockReturnValue(new Promise(() => undefined))
    render(<GoalsPage />)
    expect(screen.getByRole('status', { name: 'Loading' })).toBeInTheDocument()
  })

  it('shows the API error when listing fails', async () => {
    listGoals.mockRejectedValue(new ApiError('server_error', 'Cannot load goals', 500))
    render(<GoalsPage />)
    expect(await screen.findByText('Cannot load goals')).toBeInTheDocument()
  })

  it('shows an empty state', async () => {
    listGoals.mockResolvedValue([])
    render(<GoalsPage />)
    expect(await screen.findByText(/No goals yet/)).toBeInTheDocument()
  })

  it('lists goals; only active goals have action buttons', async () => {
    listGoals.mockResolvedValue([
      goal({ id: 'g1', title: 'Active one', description: 'details', status: 'active' }),
      goal({ id: 'g2', title: 'Done one', status: 'achieved' }),
    ])
    render(<GoalsPage />)
    expect(await screen.findByText('Active one')).toBeInTheDocument()
    expect(screen.getByText('details')).toBeInTheDocument()
    expect(screen.getByText('achieved')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Mark achieved' })).toHaveLength(1)
    expect(screen.getAllByRole('button', { name: 'Archive' })).toHaveLength(1)
  })

  it('requires a title and does not submit an empty form', async () => {
    listGoals.mockResolvedValue([])
    render(<GoalsPage />)
    await screen.findByText(/No goals yet/)
    expect(screen.getByLabelText('Title')).toBeRequired()
    await userEvent.click(screen.getByRole('button', { name: 'Add goal' }))
    expect(createGoal).not.toHaveBeenCalled()
  })

  it('creates a goal, clears the form and refetches', async () => {
    listGoals.mockResolvedValueOnce([])
    listGoals.mockResolvedValueOnce([goal({ id: 'g9', title: 'New goal' })])
    createGoal.mockResolvedValue(goal({ id: 'g9', title: 'New goal' }))
    render(<GoalsPage />)
    await screen.findByText(/No goals yet/)

    await userEvent.type(screen.getByLabelText('Title'), 'New goal')
    await userEvent.type(screen.getByLabelText('Description (optional)'), '   ')
    await userEvent.click(screen.getByRole('button', { name: 'Add goal' }))

    expect(await screen.findByRole('heading', { name: 'New goal' })).toBeInTheDocument()
    // whitespace-only description is dropped
    expect(createGoal).toHaveBeenCalledWith({ title: 'New goal', description: undefined })
    expect(screen.getByLabelText('Title')).toHaveValue('')
    expect(listGoals).toHaveBeenCalledTimes(2)
  })

  it('shows the API error when creation fails and keeps the input', async () => {
    listGoals.mockResolvedValue([])
    createGoal.mockRejectedValue(new ApiError('validation_error', 'Title too long', 422))
    render(<GoalsPage />)
    await screen.findByText(/No goals yet/)

    await userEvent.type(screen.getByLabelText('Title'), 'x')
    await userEvent.click(screen.getByRole('button', { name: 'Add goal' }))

    expect(await screen.findByText('Title too long')).toBeInTheDocument()
    expect(screen.getByLabelText('Title')).toHaveValue('x')
  })

  it('shows a generic message when creation fails with a non-API error', async () => {
    listGoals.mockResolvedValue([])
    createGoal.mockRejectedValue(new Error('network'))
    render(<GoalsPage />)
    await screen.findByText(/No goals yet/)
    await userEvent.type(screen.getByLabelText('Title'), 'x')
    await userEvent.click(screen.getByRole('button', { name: 'Add goal' }))
    expect(await screen.findByText('Could not create goal')).toBeInTheDocument()
  })

  it('marks a goal as achieved and refetches', async () => {
    listGoals.mockResolvedValueOnce([goal({ id: 'g1', title: 'Learn Rust' })])
    listGoals.mockResolvedValueOnce([goal({ id: 'g1', title: 'Learn Rust', status: 'achieved' })])
    updateGoalStatus.mockResolvedValue(goal({ status: 'achieved' }))
    render(<GoalsPage />)

    await userEvent.click(await screen.findByRole('button', { name: 'Mark achieved' }))

    expect(updateGoalStatus).toHaveBeenCalledWith('g1', 'achieved')
    expect(await screen.findByText('achieved')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Mark achieved' })).not.toBeInTheDocument()
  })

  it('archives a goal', async () => {
    listGoals.mockResolvedValue([goal({ id: 'g1' })])
    updateGoalStatus.mockResolvedValue(goal({ status: 'archived' }))
    render(<GoalsPage />)
    await userEvent.click(await screen.findByRole('button', { name: 'Archive' }))
    expect(updateGoalStatus).toHaveBeenCalledWith('g1', 'archived')
  })
})

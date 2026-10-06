import { render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AchievementsPage } from '@/pages/achievements-page'
import { gamificationService } from '@/services/gamification-service'
import { ApiError } from '@/services/api-client'
import type { AchievementProgress, QuestProgress } from '@/types/api'

vi.mock('@/services/gamification-service', () => ({
  gamificationService: { listAchievements: vi.fn(), listQuests: vi.fn() },
}))

const svc = vi.mocked(gamificationService)

const achievement = (name: string, earned: boolean): AchievementProgress => ({
  achievement: {
    id: name,
    code: name,
    name,
    description: `${name} desc`,
    icon: null,
    criteria_type: 'x',
    criteria_value: 1,
    xp_reward: 50,
  },
  earned,
  earned_at: earned ? '2026-01-02T00:00:00Z' : null,
})

const quest: QuestProgress = {
  quest: {
    id: 'q1',
    code: 'q1',
    title: 'Study 3 times',
    description: 'Log sessions',
    criteria_type: 'x',
    criteria_value: 3,
    period: 'weekly',
    xp_reward: 30,
  },
  progress: 1,
  target: 3,
  completed: false,
  period_key: '2026-W01',
}

beforeEach(() => vi.resetAllMocks())

describe('AchievementsPage', () => {
  it('renders unlocked and locked achievements plus quest progress', async () => {
    svc.listAchievements.mockResolvedValue([achievement('First step', true), achievement('Master', false)])
    svc.listQuests.mockResolvedValue([quest])
    render(<AchievementsPage />)

    expect(await screen.findByText('1 / 2 unlocked')).toBeInTheDocument()
    expect(screen.getByText('Unlocked')).toBeInTheDocument()
    expect(screen.getByText('Locked')).toBeInTheDocument()
    const bar = screen.getByRole('progressbar', { name: 'Study 3 times progress' })
    expect(bar).toHaveAttribute('aria-valuenow', '1')
    expect(within(bar.parentElement as HTMLElement).getByText('1 / 3')).toBeInTheDocument()
  })

  it('shows empty states', async () => {
    svc.listAchievements.mockResolvedValue([])
    svc.listQuests.mockResolvedValue([])
    render(<AchievementsPage />)
    expect(await screen.findByText('No quests available right now.')).toBeInTheDocument()
    expect(screen.getByText('No achievements defined yet.')).toBeInTheDocument()
  })

  it('shows an error for a failing section without hiding the other', async () => {
    svc.listAchievements.mockRejectedValue(new ApiError('server_error', 'Boom', 500))
    svc.listQuests.mockResolvedValue([quest])
    render(<AchievementsPage />)
    expect(await screen.findByText('Boom')).toBeInTheDocument()
    expect(screen.getByText('Study 3 times')).toBeInTheDocument()
  })
})

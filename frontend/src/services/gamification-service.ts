import { apiClient } from '@/services/api-client'
import type { AchievementProgress, GamificationProfile, QuestProgress } from '@/types/api'

export const gamificationService = {
  getProfile: () => apiClient.get<GamificationProfile>('/api/v1/gamification/profile'),
  listAchievements: () => apiClient.get<AchievementProgress[]>('/api/v1/gamification/achievements'),
  listQuests: () => apiClient.get<QuestProgress[]>('/api/v1/gamification/quests'),
}

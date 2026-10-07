import { apiClient } from '@/services/api-client'
import type { Recommendation } from '@/types/api'

export const recommendationService = {
  /** Deterministic "what to study today" list; the reason is in the user's language. */
  getToday: async (limit?: number): Promise<Recommendation[]> => {
    const query = limit ? `?limit=${limit}` : ''
    const body = await apiClient.get<{ items: Recommendation[] }>(
      `/api/v1/recommendations/today${query}`,
    )
    return body.items
  },
}

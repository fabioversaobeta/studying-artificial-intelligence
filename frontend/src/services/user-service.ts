import { apiClient } from '@/services/api-client'
import type { Language, User } from '@/types/api'

export const userService = {
  /** PATCH /users/me — only the provided fields change. */
  updateMe: (input: { display_name?: string; preferred_language?: Language }) =>
    apiClient.patch<User>('/api/v1/users/me', input),
}

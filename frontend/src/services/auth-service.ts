import { apiClient } from '@/services/api-client'
import { tokenStorage } from '@/lib/token-storage'
import type { TokenResponse, User } from '@/types/api'

export const authService = {
  async register(email: string, password: string, displayName: string): Promise<void> {
    const tokens = await apiClient.post<TokenResponse>(
      '/api/v1/auth/register',
      { email, password, display_name: displayName },
      true,
    )
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token)
  },

  async login(email: string, password: string): Promise<void> {
    const tokens = await apiClient.post<TokenResponse>(
      '/api/v1/auth/login',
      { email, password },
      true,
    )
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token)
  },

  logout(): void {
    tokenStorage.clear()
  },

  me(): Promise<User> {
    return apiClient.get<User>('/api/v1/auth/me')
  },

  isAuthenticated(): boolean {
    return tokenStorage.getAccessToken() !== null
  },
}

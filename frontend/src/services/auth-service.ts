import { apiClient } from '@/services/api-client'
import { tokenStorage } from '@/lib/token-storage'
import type { RegistrationInfo, TokenResponse, User } from '@/types/api'

export const authService = {
  registrationInfo(): Promise<RegistrationInfo> {
    return apiClient.get<RegistrationInfo>('/api/v1/auth/registration-info')
  },

  async register(
    email: string,
    password: string,
    displayName: string,
    inviteCode?: string,
  ): Promise<void> {
    const tokens = await apiClient.post<TokenResponse>(
      '/api/v1/auth/register',
      { email, password, display_name: displayName, invite_code: inviteCode || undefined },
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

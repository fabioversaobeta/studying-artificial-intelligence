import { apiClient, postWithBearer } from '@/services/api-client'
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

  /**
   * Clears the local session immediately, then revokes the tokens server-side
   * on a best-effort basis: a network or server failure never blocks logout.
   */
  async logout(): Promise<void> {
    const accessToken = tokenStorage.getAccessToken()
    const refreshToken = tokenStorage.getRefreshToken()
    tokenStorage.clear()
    if (!accessToken) return
    try {
      await postWithBearer('/api/v1/auth/logout', accessToken, { refresh_token: refreshToken })
    } catch {
      // Tokens are already gone locally; the server-side revocation is best-effort.
    }
  },

  me(): Promise<User> {
    return apiClient.get<User>('/api/v1/auth/me')
  },

  isAuthenticated(): boolean {
    return tokenStorage.getAccessToken() !== null
  },
}

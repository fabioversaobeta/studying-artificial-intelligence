import { apiClient, postLogout, restoreSession } from '@/services/api-client'
import { session } from '@/lib/session'
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
    session.setAccessToken(tokens.access_token)
  },

  async login(email: string, password: string): Promise<void> {
    const tokens = await apiClient.post<TokenResponse>(
      '/api/v1/auth/login',
      { email, password },
      true,
    )
    session.setAccessToken(tokens.access_token)
  },

  /**
   * Restores the session on page load from the HttpOnly refresh cookie (the
   * access token is memory-only, so a reload starts without one).
   */
  restoreSession,

  /**
   * Clears the local session immediately, then revokes the cookie's refresh
   * token (and the access token) server-side on a best-effort basis: a network
   * or server failure never blocks logout. Always calls the server, even with
   * no access token in memory, so the refresh cookie is expired.
   */
  async logout(): Promise<void> {
    const accessToken = session.getAccessToken()
    session.clear()
    try {
      await postLogout(accessToken)
    } catch {
      // Local state is already gone; the server-side revocation is best-effort.
    }
  },

  me(): Promise<User> {
    return apiClient.get<User>('/api/v1/auth/me')
  },

  isAuthenticated(): boolean {
    return session.hasAccessToken()
  },
}

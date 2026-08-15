// Tokens live in localStorage: simplest option for a single-user personal
// app with no XSS-hostile third-party scripts. See docs/PENDING.md for the
// tradeoffs (no server-side revocation) if this ever needs to harden.

const ACCESS_TOKEN_KEY = 'learning_platform.access_token'
const REFRESH_TOKEN_KEY = 'learning_platform.refresh_token'

export const tokenStorage = {
  getAccessToken: (): string | null => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY),
  setTokens: (accessToken: string, refreshToken: string): void => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  },
  clear: (): void => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

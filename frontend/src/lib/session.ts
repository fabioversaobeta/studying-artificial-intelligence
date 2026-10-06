// The access token lives ONLY in this module's memory: never in localStorage,
// sessionStorage, IndexedDB or a cookie, so an XSS payload cannot read it from
// storage and it disappears with the tab. The long-lived refresh token is an
// HttpOnly cookie the browser manages; JavaScript never sees it. A page load
// restores the session by calling POST /auth/refresh (see api-client.ts).
// Rationale and trade-offs: docs/DECISIONS.md, "Tokens: in-memory access token
// plus HttpOnly refresh cookie".

let accessToken: string | null = null

export const session = {
  getAccessToken: (): string | null => accessToken,
  setAccessToken: (token: string): void => {
    accessToken = token
  },
  hasAccessToken: (): boolean => accessToken !== null,
  clear: (): void => {
    accessToken = null
  },
}

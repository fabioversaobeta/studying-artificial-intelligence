import type { ApiErrorBody, TokenResponse } from '@/types/api'
import { session } from '@/lib/session'

// Empty (the default) means same origin: the browser calls /api/... on the page's
// own origin, served by the Vite dev proxy locally and by the Vercel rewrite in
// production, which keeps the refresh cookie first-party. Set VITE_API_URL only
// to point at a different origin (cookies then need SameSite=None; see
// docs/DEPLOYMENT.md).
const API_BASE_URL: string = import.meta.env.VITE_API_URL ?? ''

// Required by the backend on the cookie-authenticated endpoints (/auth/refresh and
// /auth/logout). A custom header cannot be sent cross-site without a CORS
// preflight that the API only approves for its own frontend origins (CSRF defence).
const CSRF_HEADERS = { 'X-CSRF-Protection': '1' }
const REFRESH_LOCK_NAME = 'learning_platform.refresh'

export class ApiError extends Error {
  code: string
  status: number

  constructor(code: string, message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

let refreshPromise: Promise<void> | null = null

async function requestNewAccessToken(): Promise<void> {
  // The refresh token is an HttpOnly cookie: the browser attaches it, and the
  // server rotates it (Set-Cookie) in the response.
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: CSRF_HEADERS,
    credentials: 'include',
  })

  if (!response.ok) {
    session.clear()
    throw new ApiError('authentication_error', 'Session expired', 401)
  }

  const body = (await response.json()) as TokenResponse
  session.setAccessToken(body.access_token)
}

function refreshAccessToken(): Promise<void> {
  // Rotation burns the cookie's token on use, and tabs share one cookie jar. Two
  // tabs refreshing at the same instant would present the same token twice, which
  // the server treats as theft and revokes every session. The Web Lock serialises
  // refreshes across tabs (the second one sends the cookie the first one rotated).
  if (typeof navigator !== 'undefined' && navigator.locks) {
    return navigator.locks.request(REFRESH_LOCK_NAME, requestNewAccessToken)
  }
  return requestNewAccessToken()
}

/** Refresh once at a time within this tab, however many callers ask. */
function sharedRefresh(): Promise<void> {
  refreshPromise ??= refreshAccessToken().finally(() => {
    refreshPromise = null
  })
  return refreshPromise
}

/**
 * Page-load session restore: with no access token in memory, ask the server for
 * one using the refresh cookie. Resolves false (never throws) when there is no
 * valid session.
 */
export async function restoreSession(): Promise<boolean> {
  if (session.hasAccessToken()) return true
  try {
    await sharedRefresh()
    return true
  } catch {
    return false
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  skipAuth?: boolean
}

export interface Paged<T> {
  items: T[]
  /** Total matching rows (`X-Total-Count`); falls back to `items.length` when absent. */
  total: number
}

export interface PageParams {
  limit?: number
  offset?: number
}

interface RawResult<T> {
  data: T
  headers: Headers
}

async function send<T>(
  path: string,
  options: RequestOptions = {},
  isRetry = false,
): Promise<RawResult<T>> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }

  if (!options.skipAuth) {
    const accessToken = session.getAccessToken()
    if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    // Login/register/refresh set or rotate the refresh cookie. Same-origin by
    // default; 'include' also covers a deliberate cross-origin VITE_API_URL.
    credentials: 'include',
  })

  if (response.status === 401 && !options.skipAuth && !isRetry) {
    try {
      await sharedRefresh()
      return send<T>(path, options, true)
    } catch {
      // fall through to normal error handling below
    }
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorBody | null
    throw new ApiError(
      body?.error?.code ?? 'unknown_error',
      body?.error?.message ?? `Request failed with status ${response.status}`,
      response.status,
    )
  }

  if (response.status === 204) return { data: undefined as T, headers: response.headers }
  return { data: (await response.json()) as T, headers: response.headers }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return (await send<T>(path, options)).data
}

function withPageParams(path: string, params: PageParams): string {
  const query = new URLSearchParams()
  if (params.limit !== undefined) query.set('limit', String(params.limit))
  if (params.offset !== undefined) query.set('offset', String(params.offset))
  const qs = query.toString()
  if (!qs) return path
  return `${path}${path.includes('?') ? '&' : '?'}${qs}`
}

/**
 * POST /auth/logout: revokes the refresh cookie server-side and expires it, plus
 * the given access token when there is one. Bypasses the refresh-on-401 flow
 * (logout clears the local session first and must not trigger a refresh).
 */
export async function postLogout(accessToken: string | null): Promise<void> {
  const headers: Record<string, string> = { ...CSRF_HEADERS }
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
    method: 'POST',
    headers,
    credentials: 'include',
  })
  if (!response.ok) throw new ApiError('unknown_error', `Request failed`, response.status)
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  /** GET a paginated list: body is an array, total comes from `X-Total-Count`. */
  getPaged: async <T>(path: string, params: PageParams = {}): Promise<Paged<T>> => {
    const { data, headers } = await send<T[]>(withPageParams(path, params), { method: 'GET' })
    const header = Number.parseInt(headers.get('X-Total-Count') ?? '', 10)
    return { items: data, total: Number.isFinite(header) ? header : data.length }
  },
  post: <T>(path: string, body?: unknown, skipAuth = false) =>
    request<T>(path, { method: 'POST', body, skipAuth }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
}

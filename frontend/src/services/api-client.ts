import type { ApiErrorBody, TokenResponse } from '@/types/api'
import { tokenStorage } from '@/lib/token-storage'

const API_BASE_URL: string = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

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

async function refreshAccessToken(): Promise<void> {
  const refreshToken = tokenStorage.getRefreshToken()
  if (!refreshToken) throw new ApiError('authentication_error', 'Not authenticated', 401)

  const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!response.ok) {
    tokenStorage.clear()
    throw new ApiError('authentication_error', 'Session expired', 401)
  }

  const body = (await response.json()) as TokenResponse
  tokenStorage.setTokens(body.access_token, body.refresh_token)
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
    const accessToken = tokenStorage.getAccessToken()
    if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  if (response.status === 401 && !options.skipAuth && !isRetry) {
    refreshPromise ??= refreshAccessToken().finally(() => {
      refreshPromise = null
    })
    try {
      await refreshPromise
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
 * Fire a request with explicitly supplied credentials, bypassing the stored
 * tokens and the refresh-on-401 flow. Used by logout, which clears storage
 * first and must not trigger a refresh with the tokens it is revoking.
 */
export async function postWithBearer(path: string, accessToken: string, body: unknown) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify(body),
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

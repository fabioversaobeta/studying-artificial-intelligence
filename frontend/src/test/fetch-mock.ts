import { vi } from 'vitest'

type Reply = { status?: number; body?: unknown }
type Handler = (init: RequestInit) => Reply | Promise<Reply>

/**
 * Stubs global `fetch` with a route table keyed by "METHOD /path".
 * Unmatched requests reject loudly (like a network error) so tests never
 * hit the real network. The page-load session restore (POST /auth/refresh)
 * answers 401 ("no session cookie") unless a test overrides it.
 */
export function mockFetch(routes: Record<string, Handler | Reply>) {
  const table: Record<string, Handler | Reply> = {
    'POST /api/v1/auth/refresh': apiError(401, 'authentication_error', 'Missing refresh token'),
    ...routes,
  }
  const fn = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    // API paths are same-origin relative ('/api/...'), so resolve against a dummy base.
    const path = new URL(String(input), 'http://localhost').pathname
    const key = `${init.method ?? 'GET'} ${path}`
    const route = table[key]
    if (!route) throw new Error(`Unmocked request: ${key}`)
    const { status = 200, body } = typeof route === 'function' ? await route(init) : route
    return new Response(status === 204 ? null : JSON.stringify(body ?? {}), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

export function apiError(status: number, code: string, message: string) {
  return { status, body: { error: { code, message } } }
}

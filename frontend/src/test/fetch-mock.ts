import { vi } from 'vitest'

type Reply = { status?: number; body?: unknown }
type Handler = (init: RequestInit) => Reply

/**
 * Stubs global `fetch` with a route table keyed by "METHOD /path".
 * Unmatched requests reject loudly (like a network error) so tests never
 * hit the real network.
 */
export function mockFetch(routes: Record<string, Handler | Reply>) {
  const fn = vi.fn((input: RequestInfo | URL, init: RequestInit = {}) => {
    const path = new URL(String(input)).pathname
    const key = `${init.method ?? 'GET'} ${path}`
    const route = routes[key]
    if (!route) return Promise.reject(new Error(`Unmocked request: ${key}`))
    const { status = 200, body } = typeof route === 'function' ? route(init) : route
    return Promise.resolve(
      new Response(status === 204 ? null : JSON.stringify(body ?? {}), {
        status,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

export function apiError(status: number, code: string, message: string) {
  return { status, body: { error: { code, message } } }
}

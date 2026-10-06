import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiClient, postLogout, restoreSession } from '@/services/api-client'
import { session } from '@/lib/session'

const fetchMock = vi.fn<typeof fetch>()

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function headersOf(call: unknown[]): Record<string, string> {
  return (call[1] as RequestInit).headers as Record<string, string>
}

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

describe('apiClient', () => {
  it('sends the Authorization header when an access token exists', async () => {
    session.setAccessToken('acc')
    fetchMock.mockResolvedValueOnce(json({ ok: true }))

    await expect(apiClient.get('/api/v1/things')).resolves.toEqual({ ok: true })

    expect(headersOf(fetchMock.mock.calls[0])['Authorization']).toBe('Bearer acc')
  })

  it('omits Authorization when there is no token or when skipAuth is set', async () => {
    fetchMock.mockImplementation(async () => json({}))
    await apiClient.get('/a')
    expect(headersOf(fetchMock.mock.calls[0])['Authorization']).toBeUndefined()

    session.setAccessToken('acc')
    await apiClient.post('/b', { x: 1 }, true)
    expect(headersOf(fetchMock.mock.calls[1])['Authorization']).toBeUndefined()
    expect((fetchMock.mock.calls[1][1] as RequestInit).body).toBe('{"x":1}')
  })

  it('returns undefined for 204 responses', async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }))
    await expect(apiClient.patch('/x', {})).resolves.toBeUndefined()
  })

  it('parses the {error:{code,message}} body into an ApiError', async () => {
    fetchMock.mockResolvedValueOnce(
      json({ error: { code: 'validation_error', message: 'Bad input' } }, 422),
    )
    const err = await apiClient.get('/x').catch((e: unknown) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({ code: 'validation_error', message: 'Bad input', status: 422 })
  })

  it('falls back to unknown_error when the error body is not JSON', async () => {
    fetchMock.mockResolvedValueOnce(new Response('oops', { status: 500 }))
    const err = await apiClient.get('/x').catch((e: unknown) => e)
    expect(err).toMatchObject({
      code: 'unknown_error',
      message: 'Request failed with status 500',
      status: 500,
    })
  })

  describe('401 handling', () => {
    it('refreshes the token once and retries the request', async () => {
      session.setAccessToken('old')
      fetchMock
        .mockResolvedValueOnce(json({}, 401))
        .mockResolvedValueOnce(json({ access_token: 'new' }))
        .mockResolvedValueOnce(json({ data: 1 }))

      await expect(apiClient.get('/x')).resolves.toEqual({ data: 1 })

      expect(fetchMock).toHaveBeenCalledTimes(3)
      const refreshCall = fetchMock.mock.calls[1]
      expect(String(refreshCall[0])).toContain('/api/v1/auth/refresh')
      const refreshInit = refreshCall[1] as RequestInit
      // The refresh token travels as an HttpOnly cookie: no body, credentials included,
      // plus the CSRF header the backend requires.
      expect(refreshInit.body).toBeUndefined()
      expect(refreshInit.credentials).toBe('include')
      expect(headersOf(refreshCall)['X-CSRF-Protection']).toBe('1')
      expect(headersOf(fetchMock.mock.calls[2])['Authorization']).toBe('Bearer new')
      expect(session.getAccessToken()).toBe('new')
      expect(localStorage.length).toBe(0)
    })

    it('deduplicates the refresh across concurrent 401s', async () => {
      session.setAccessToken('old')
      let refreshCalls = 0
      fetchMock.mockImplementation(async (input, init) => {
        const url = String(input)
        if (url.includes('/auth/refresh')) {
          refreshCalls += 1
          await new Promise((r) => setTimeout(r, 10))
          return json({ access_token: 'new' })
        }
        const auth = (init?.headers as Record<string, string> | undefined)?.['Authorization']
        return auth === 'Bearer new' ? json({ url }) : json({}, 401)
      })

      const results = await Promise.all([
        apiClient.get('/a'),
        apiClient.get('/b'),
        apiClient.get('/c'),
      ])

      expect(refreshCalls).toBe(1)
      expect(results).toHaveLength(3)
    })

    it('retries only once: a second 401 surfaces as an ApiError', async () => {
      session.setAccessToken('old')
      fetchMock
        .mockResolvedValueOnce(json({}, 401))
        .mockResolvedValueOnce(json({ access_token: 'new' }))
        .mockResolvedValueOnce(
          json({ error: { code: 'authentication_error', message: 'Nope' } }, 401),
        )

      await expect(apiClient.get('/x')).rejects.toMatchObject({ status: 401, message: 'Nope' })
      expect(fetchMock).toHaveBeenCalledTimes(3)
    })

    it('clears the access token and throws ApiError when the refresh fails', async () => {
      session.setAccessToken('old')
      fetchMock
        .mockResolvedValueOnce(
          json({ error: { code: 'authentication_error', message: 'Expired' } }, 401),
        )
        .mockResolvedValueOnce(json({}, 401))

      const err = await apiClient.get('/x').catch((e: unknown) => e)

      expect(err).toBeInstanceOf(ApiError)
      expect(err).toMatchObject({ code: 'authentication_error', status: 401 })
      expect(session.getAccessToken()).toBeNull()
    })

    it('does not attempt a refresh when skipAuth is set', async () => {
      fetchMock.mockResolvedValueOnce(
        json({ error: { code: 'authentication_error', message: 'Bad creds' } }, 401),
      )
      await expect(apiClient.post('/login', {}, true)).rejects.toMatchObject({
        message: 'Bad creds',
      })
      expect(fetchMock).toHaveBeenCalledTimes(1)
    })

    it('tries the refresh cookie even with no access token, then surfaces the 401', async () => {
      // e.g. a logged-out visitor hitting an authenticated endpoint: no cookie, refresh 401s.
      fetchMock.mockResolvedValueOnce(json({}, 401)).mockResolvedValueOnce(json({}, 401))
      await expect(apiClient.get('/x')).rejects.toBeInstanceOf(ApiError)
      expect(fetchMock).toHaveBeenCalledTimes(2)
      expect(String(fetchMock.mock.calls[1][0])).toContain('/api/v1/auth/refresh')
    })

    it('keeps the access token when the refresh fails because the network is down', async () => {
      session.setAccessToken('old')
      fetchMock.mockResolvedValueOnce(json({}, 401)).mockRejectedValueOnce(new TypeError('offline'))
      await expect(apiClient.get('/x')).rejects.toBeInstanceOf(ApiError)
      expect(session.getAccessToken()).toBe('old')
    })
  })

  it('sends requests with credentials and a same-origin (relative) URL by default', async () => {
    fetchMock.mockResolvedValueOnce(json({}))
    await apiClient.get('/api/v1/things')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/things')
    expect((fetchMock.mock.calls[0][1] as RequestInit).credentials).toBe('include')
  })

  describe('restoreSession', () => {
    it('gets an access token from the refresh cookie and keeps it only in memory', async () => {
      fetchMock.mockResolvedValueOnce(json({ access_token: 'restored', token_type: 'bearer' }))
      await expect(restoreSession()).resolves.toBe(true)
      expect(session.getAccessToken()).toBe('restored')
      expect(localStorage.length).toBe(0)
      expect(sessionStorage.length).toBe(0)
    })

    it('resolves false when there is no valid session cookie', async () => {
      fetchMock.mockResolvedValueOnce(json({}, 401))
      await expect(restoreSession()).resolves.toBe(false)
      expect(session.hasAccessToken()).toBe(false)
    })

    it('resolves false (does not throw) when the network fails', async () => {
      fetchMock.mockRejectedValueOnce(new TypeError('offline'))
      await expect(restoreSession()).resolves.toBe(false)
    })

    it('does not call the server when an access token is already in memory', async () => {
      session.setAccessToken('acc')
      await expect(restoreSession()).resolves.toBe(true)
      expect(fetchMock).not.toHaveBeenCalled()
    })

    it('shares one refresh between concurrent restores and 401 retries', async () => {
      let refreshCalls = 0
      fetchMock.mockImplementation(async (input) => {
        if (String(input).includes('/auth/refresh')) {
          refreshCalls += 1
          await new Promise((r) => setTimeout(r, 10))
          return json({ access_token: 'new' })
        }
        return json({})
      })
      await Promise.all([restoreSession(), restoreSession()])
      expect(refreshCalls).toBe(1)
    })

    it('serialises refreshes across tabs with a Web Lock when available', async () => {
      const request = vi.fn(async (_name: string, cb: () => Promise<void>) => cb())
      vi.stubGlobal('navigator', { locks: { request } })
      fetchMock.mockResolvedValueOnce(json({ access_token: 'locked' }))
      await expect(restoreSession()).resolves.toBe(true)
      expect(request).toHaveBeenCalledTimes(1)
      expect(request.mock.calls[0][0]).toBe('learning_platform.refresh')
      vi.unstubAllGlobals()
    })
  })

  describe('postLogout', () => {
    it('posts with credentials, the CSRF header and the bearer token when present', async () => {
      fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }))
      await postLogout('acc')
      const [url, init] = fetchMock.mock.calls[0]
      expect(String(url)).toBe('/api/v1/auth/logout')
      expect((init as RequestInit).credentials).toBe('include')
      expect((init as RequestInit).body).toBeUndefined()
      expect(headersOf(fetchMock.mock.calls[0])['X-CSRF-Protection']).toBe('1')
      expect(headersOf(fetchMock.mock.calls[0])['Authorization']).toBe('Bearer acc')
    })

    it('omits Authorization without an access token', async () => {
      fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }))
      await postLogout(null)
      expect(headersOf(fetchMock.mock.calls[0])['Authorization']).toBeUndefined()
    })

    it('throws on a failed response', async () => {
      fetchMock.mockResolvedValueOnce(json({}, 500))
      await expect(postLogout('acc')).rejects.toBeInstanceOf(ApiError)
    })
  })

  describe('getPaged', () => {
    it('reads the total from X-Total-Count and sends limit/offset', async () => {
      fetchMock.mockResolvedValueOnce(
        new Response(JSON.stringify([{ id: 1 }, { id: 2 }]), {
          status: 200,
          headers: { 'Content-Type': 'application/json', 'X-Total-Count': '57' },
        }),
      )
      const page = await apiClient.getPaged<{ id: number }>('/api/v1/goals', {
        limit: 2,
        offset: 4,
      })
      expect(page).toEqual({ items: [{ id: 1 }, { id: 2 }], total: 57 })
      expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/api\/v1\/goals\?limit=2&offset=4$/)
    })

    it('falls back to items.length without the header and appends to existing queries', async () => {
      fetchMock.mockResolvedValueOnce(json([1, 2, 3]))
      const page = await apiClient.getPaged<number>('/x?status=active', { limit: 10 })
      expect(page).toEqual({ items: [1, 2, 3], total: 3 })
      expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/x\?status=active&limit=10$/)
    })

    it('uses the path untouched with no params and still refreshes on 401', async () => {
      session.setAccessToken('old')
      fetchMock
        .mockResolvedValueOnce(json({}, 401))
        .mockResolvedValueOnce(json({ access_token: 'new' }))
        .mockResolvedValueOnce(json([]))
      const page = await apiClient.getPaged('/y')
      expect(page).toEqual({ items: [], total: 0 })
      expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/y$/)
    })

    it('throws ApiError on failure', async () => {
      fetchMock.mockResolvedValueOnce(json({ error: { code: 'validation_error', message: 'Bad' } }, 422))
      await expect(apiClient.getPaged('/y', { limit: 0 })).rejects.toBeInstanceOf(ApiError)
    })
  })
})

import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiClient } from '@/services/api-client'
import { tokenStorage } from '@/lib/token-storage'

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
    tokenStorage.setTokens('acc', 'ref')
    fetchMock.mockResolvedValueOnce(json({ ok: true }))

    await expect(apiClient.get('/api/v1/things')).resolves.toEqual({ ok: true })

    expect(headersOf(fetchMock.mock.calls[0])['Authorization']).toBe('Bearer acc')
  })

  it('omits Authorization when there is no token or when skipAuth is set', async () => {
    fetchMock.mockImplementation(async () => json({}))
    await apiClient.get('/a')
    expect(headersOf(fetchMock.mock.calls[0])['Authorization']).toBeUndefined()

    tokenStorage.setTokens('acc', 'ref')
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
      tokenStorage.setTokens('old', 'ref')
      fetchMock
        .mockResolvedValueOnce(json({}, 401))
        .mockResolvedValueOnce(json({ access_token: 'new', refresh_token: 'ref2' }))
        .mockResolvedValueOnce(json({ data: 1 }))

      await expect(apiClient.get('/x')).resolves.toEqual({ data: 1 })

      expect(fetchMock).toHaveBeenCalledTimes(3)
      expect(String(fetchMock.mock.calls[1][0])).toContain('/api/v1/auth/refresh')
      expect(JSON.parse((fetchMock.mock.calls[1][1] as RequestInit).body as string)).toEqual({
        refresh_token: 'ref',
      })
      expect(headersOf(fetchMock.mock.calls[2])['Authorization']).toBe('Bearer new')
      expect(tokenStorage.getRefreshToken()).toBe('ref2')
    })

    it('deduplicates the refresh across concurrent 401s', async () => {
      tokenStorage.setTokens('old', 'ref')
      let refreshCalls = 0
      fetchMock.mockImplementation(async (input, init) => {
        const url = String(input)
        if (url.includes('/auth/refresh')) {
          refreshCalls += 1
          await new Promise((r) => setTimeout(r, 10))
          return json({ access_token: 'new', refresh_token: 'ref2' })
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
      tokenStorage.setTokens('old', 'ref')
      fetchMock
        .mockResolvedValueOnce(json({}, 401))
        .mockResolvedValueOnce(json({ access_token: 'new', refresh_token: 'ref2' }))
        .mockResolvedValueOnce(
          json({ error: { code: 'authentication_error', message: 'Nope' } }, 401),
        )

      await expect(apiClient.get('/x')).rejects.toMatchObject({ status: 401, message: 'Nope' })
      expect(fetchMock).toHaveBeenCalledTimes(3)
    })

    it('clears tokens and throws ApiError when the refresh fails', async () => {
      tokenStorage.setTokens('old', 'ref')
      fetchMock
        .mockResolvedValueOnce(
          json({ error: { code: 'authentication_error', message: 'Expired' } }, 401),
        )
        .mockResolvedValueOnce(json({}, 401))

      const err = await apiClient.get('/x').catch((e: unknown) => e)

      expect(err).toBeInstanceOf(ApiError)
      expect(err).toMatchObject({ code: 'authentication_error', status: 401 })
      expect(tokenStorage.getAccessToken()).toBeNull()
      expect(tokenStorage.getRefreshToken()).toBeNull()
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

    it('throws without calling refresh when there is no refresh token', async () => {
      fetchMock.mockResolvedValueOnce(json({}, 401))
      await expect(apiClient.get('/x')).rejects.toBeInstanceOf(ApiError)
      expect(fetchMock).toHaveBeenCalledTimes(1)
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
      tokenStorage.setTokens('old', 'ref')
      fetchMock
        .mockResolvedValueOnce(json({}, 401))
        .mockResolvedValueOnce(json({ access_token: 'new', refresh_token: 'ref2' }))
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

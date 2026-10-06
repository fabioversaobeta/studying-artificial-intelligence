import { describe, expect, it } from 'vitest'
import { session } from '@/lib/session'

describe('session (in-memory access token)', () => {
  it('starts empty', () => {
    expect(session.getAccessToken()).toBeNull()
    expect(session.hasAccessToken()).toBe(false)
  })

  it('stores, overwrites and clears the token', () => {
    session.setAccessToken('a1')
    expect(session.getAccessToken()).toBe('a1')
    expect(session.hasAccessToken()).toBe(true)
    session.setAccessToken('a2')
    expect(session.getAccessToken()).toBe('a2')
    session.clear()
    expect(session.getAccessToken()).toBeNull()
  })

  it('never writes to any web storage', () => {
    session.setAccessToken('secret-access-token')
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
    expect(JSON.stringify({ ...localStorage })).not.toContain('secret-access-token')
    expect(document.cookie).not.toContain('secret-access-token')
  })
})

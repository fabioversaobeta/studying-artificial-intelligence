import { describe, expect, it } from 'vitest'
import { tokenStorage } from '@/lib/token-storage'

describe('tokenStorage', () => {
  it('returns null when nothing is stored', () => {
    expect(tokenStorage.getAccessToken()).toBeNull()
    expect(tokenStorage.getRefreshToken()).toBeNull()
  })

  it('stores and reads both tokens', () => {
    tokenStorage.setTokens('access-1', 'refresh-1')
    expect(tokenStorage.getAccessToken()).toBe('access-1')
    expect(tokenStorage.getRefreshToken()).toBe('refresh-1')
  })

  it('overwrites existing tokens', () => {
    tokenStorage.setTokens('a1', 'r1')
    tokenStorage.setTokens('a2', 'r2')
    expect(tokenStorage.getAccessToken()).toBe('a2')
    expect(tokenStorage.getRefreshToken()).toBe('r2')
  })

  it('clear removes both tokens', () => {
    tokenStorage.setTokens('a', 'r')
    tokenStorage.clear()
    expect(tokenStorage.getAccessToken()).toBeNull()
    expect(tokenStorage.getRefreshToken()).toBeNull()
  })
})

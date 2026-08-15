import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { authService } from '@/services/auth-service'
import type { User } from '@/types/api'
import { AuthContext } from '@/features/auth/auth-context-value'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadUser = useCallback(async () => {
    if (!authService.isAuthenticated()) {
      setUser(null)
      setIsLoading(false)
      return
    }
    try {
      const currentUser = await authService.me()
      setUser(currentUser)
    } catch {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadUser()
  }, [loadUser])

  const login = useCallback(
    async (email: string, password: string) => {
      await authService.login(email, password)
      await loadUser()
    },
    [loadUser],
  )

  const register = useCallback(
    async (email: string, password: string, displayName: string) => {
      await authService.register(email, password, displayName)
      await loadUser()
    },
    [loadUser],
  )

  const logout = useCallback(() => {
    authService.logout()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

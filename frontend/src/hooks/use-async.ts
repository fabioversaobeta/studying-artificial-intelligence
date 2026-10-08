import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '@/services/api-client'
import { useT } from '@/i18n/use-i18n'

interface AsyncState<T> {
  data: T | null
  error: string | null
  isLoading: boolean
}

/**
 * Fetches `fn()` on mount and whenever `deps` change. Exposes `refetch` for
 * manual re-fetching after a mutation (e.g. after logging a study session).
 *
 * `isLoading` only reflects the *first* fetch (no data yet) — a `refetch()`
 * with existing data on screen updates it in place instead of unmounting
 * the tree behind a spinner, which would otherwise reset any local UI state
 * (like an expanded card) on every mutation.
 *
 * Deliberately minimal — a full query library (React Query, etc.) is more
 * than this app's data-fetching needs justify today.
 */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<AsyncState<T>>({ data: null, error: null, isLoading: true })
  const t = useT()
  const tRef = useRef(t)
  tRef.current = t

  const run = useCallback(() => {
    setState((prev) => ({ ...prev, isLoading: prev.data === null, error: null }))
    fn()
      .then((data) => setState({ data, error: null, isLoading: false }))
      .catch((err: unknown) => {
        const message = err instanceof ApiError ? err.message : tRef.current('common.somethingWrong')
        setState({ data: null, error: message, isLoading: false })
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    run()
  }, [run])

  return { ...state, refetch: run }
}

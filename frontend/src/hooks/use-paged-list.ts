import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, type Paged } from '@/services/api-client'
import { useT } from '@/i18n/use-i18n'

type FetchPage<T> = (params: { limit: number; offset: number }) => Promise<Paged<T>>

interface PagedState<T> {
  items: T[]
  total: number
  error: string | null
  isLoading: boolean
  isLoadingMore: boolean
  loadMoreError: string | null
}

function messageOf(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback
}

/**
 * Accumulating paginated list for endpoints that return an array body plus
 * an `X-Total-Count` header (see docs/API.md). `reload()` re-fetches the
 * first page (keeping current items on screen meanwhile); `loadMore()`
 * appends the next page. A failed "load more" keeps the loaded items and
 * is reported via `loadMoreError` instead of replacing the whole list.
 */
export function usePagedList<T>(fetchPage: FetchPage<T>, pageSize = 20, deps: unknown[] = []) {
  const [state, setState] = useState<PagedState<T>>({
    items: [],
    total: 0,
    error: null,
    isLoading: true,
    isLoadingMore: false,
    loadMoreError: null,
  })
  const t = useT()
  const tRef = useRef(t)
  tRef.current = t
  const fetchRef = useRef(fetchPage)
  fetchRef.current = fetchPage
  const generation = useRef(0)
  const itemsRef = useRef<T[]>([])
  itemsRef.current = state.items

  const reload = useCallback(() => {
    const gen = ++generation.current
    setState((prev) => ({
      ...prev,
      isLoading: prev.items.length === 0,
      error: null,
      loadMoreError: null,
    }))
    fetchRef
      .current({ limit: pageSize, offset: 0 })
      .then((page) => {
        if (gen !== generation.current) return
        setState((prev) => ({
          ...prev,
          items: page.items,
          total: page.total,
          isLoading: false,
          isLoadingMore: false,
        }))
      })
      .catch((err: unknown) => {
        if (gen !== generation.current) return
        setState((prev) => ({
          ...prev,
          items: [],
          total: 0,
          error: messageOf(err, tRef.current('common.somethingWrong')),
          isLoading: false,
          isLoadingMore: false,
        }))
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageSize, ...deps])

  const loadMore = useCallback(() => {
    const gen = generation.current
    const offset = itemsRef.current.length
    setState((prev) => ({ ...prev, isLoadingMore: true, loadMoreError: null }))
    fetchRef
      .current({ limit: pageSize, offset })
      .then((page) => {
        if (gen !== generation.current) return
        setState((prev) => ({
          ...prev,
          items: [...prev.items, ...page.items],
          total: page.total,
          isLoadingMore: false,
        }))
      })
      .catch((err: unknown) => {
        if (gen !== generation.current) return
        setState((prev) => ({
          ...prev,
          isLoadingMore: false,
          loadMoreError: messageOf(err, tRef.current('common.couldNotLoadMore')),
        }))
      })
  }, [pageSize])

  useEffect(() => {
    reload()
  }, [reload])

  return { ...state, hasMore: state.items.length < state.total, loadMore, reload }
}

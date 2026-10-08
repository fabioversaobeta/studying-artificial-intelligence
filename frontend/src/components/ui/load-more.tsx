import { Button } from '@/components/ui/button'
import { ErrorAlert } from '@/components/ui/alert'
import { useT } from '@/i18n/use-i18n'

interface LoadMoreProps {
  shown: number
  total: number
  hasMore: boolean
  isLoading: boolean
  error: string | null
  onLoadMore: () => void
}

/** "Showing X of Y" footer with a Load more button for paginated lists. */
export function LoadMore({ shown, total, hasMore, isLoading, error, onLoadMore }: LoadMoreProps) {
  const t = useT()
  if (total === 0) return null
  return (
    <div className="space-y-3">
      {error && <ErrorAlert message={error} />}
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-fg-muted" aria-live="polite">
          {t('common.showing', { shown, total })}
        </p>
        {hasMore && (
          <Button type="button" variant="secondary" onClick={onLoadMore} disabled={isLoading}>
            {isLoading ? t('common.loadingEllipsis') : t('common.loadMore')}
          </Button>
        )}
      </div>
    </div>
  )
}

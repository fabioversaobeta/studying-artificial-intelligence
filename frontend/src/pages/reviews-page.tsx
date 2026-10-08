import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePagedList } from '@/hooks/use-paged-list'
import { learningService } from '@/services/learning-service'
import { ApiError } from '@/services/api-client'
import type { DueReview, Review } from '@/types/api'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { LoadMore } from '@/components/ui/load-more'
import { PageSpinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { useT } from '@/i18n/use-i18n'

const RECALL_QUALITIES = [0, 1, 2, 3, 4, 5] as const

function ReviewCard({
  review,
  result,
  onSubmitted,
}: {
  review: DueReview
  result: Review | undefined
  onSubmitted: (updated: Review) => void
}) {
  const t = useT()
  const [pending, setPending] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const titleId = `review-${review.id}`

  async function submit(quality: number) {
    setPending(quality)
    setError(null)
    try {
      const updated = await learningService.submitRecall(review.competency_id, quality)
      onSubmitted(updated)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('reviews.saveError'))
    } finally {
      setPending(null)
    }
  }

  return (
    <Card aria-labelledby={titleId} role="group">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 id={titleId} className="font-medium text-heading">
            {review.competency_name}
          </h2>
          <Link
            to={`/subjects/${review.subject_id}`}
            className="text-sm text-accent-light hover:underline"
          >
            {review.subject_name}
          </Link>
        </div>
        <Badge tone={result ? 'success' : 'warning'}>{result ? t('reviews.badgeReviewed') : t('reviews.badgeDue')}</Badge>
      </div>

      {result ? (
        <p role="status" className="mt-4 text-sm text-success">
          {t('reviews.saved', {
            interval:
              result.interval_days <= 0
                ? t('reviews.laterToday')
                : t('reviews.inDays', { count: result.interval_days }),
          })}
        </p>
      ) : (
        <fieldset className="mt-4" disabled={pending !== null}>
          <legend className="mb-2 text-sm text-fg-muted">{t('reviews.recallQuestion')}</legend>
          <div className="flex flex-wrap gap-2">
            {RECALL_QUALITIES.map((quality) => (
              <Button
                key={quality}
                type="button"
                variant="secondary"
                onClick={() => submit(quality)}
              >
                {quality} · {t(`reviews.recall.${quality}`)}
              </Button>
            ))}
          </div>
          {error && (
            <div className="mt-3">
              <ErrorAlert message={error} />
            </div>
          )}
        </fieldset>
      )}
    </Card>
  )
}

export function ReviewsPage() {
  const list = usePagedList((page) => learningService.listDueReviews(page))
  const { items: data, error, isLoading, reload: refetch } = list
  const [results, setResults] = useState<Record<string, Review>>({})
  const t = useT()

  if (isLoading) return <PageSpinner />
  if (error) return <ErrorAlert message={error} onRetry={refetch} />

  const reviewedCount = data.filter((r) => results[r.id]).length
  const remaining = Math.max(0, list.total - reviewedCount)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-heading">{t('reviews.title')}</h1>
        <p className="mt-1 text-sm text-fg-muted">
          {t('reviews.subtitle')}
        </p>
      </div>

      {data.length === 0 ? (
        <Card>
          <p className="text-sm text-fg-muted">
            {t('reviews.empty')}
          </p>
        </Card>
      ) : (
        <>
          <p className="text-sm text-fg-muted" aria-live="polite">
            {remaining === 0 ? t('reviews.allCaughtUp') : t('reviews.due', { count: remaining })}
          </p>
          <div className="space-y-3">
            {data.map((review) => (
              <ReviewCard
                key={review.id}
                review={review}
                result={results[review.id]}
                onSubmitted={(updated) => setResults((prev) => ({ ...prev, [review.id]: updated }))}
              />
            ))}
          </div>
          <LoadMore
            shown={data.length}
            total={list.total}
            hasMore={list.hasMore}
            isLoading={list.isLoadingMore}
            error={list.loadMoreError}
            onLoadMore={list.loadMore}
          />
        </>
      )}
    </div>
  )
}

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAsync } from '@/hooks/use-async'
import { usePagedList } from '@/hooks/use-paged-list'
import { learningService } from '@/services/learning-service'
import { ApiError } from '@/services/api-client'
import { loadCompetencyIndex, type CompetencyRef } from '@/features/learning/competency-index'
import type { Review } from '@/types/api'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { LoadMore } from '@/components/ui/load-more'
import { PageSpinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'

const RECALL_OPTIONS = [
  { quality: 0, label: 'Blackout' },
  { quality: 1, label: 'Wrong' },
  { quality: 2, label: 'Almost' },
  { quality: 3, label: 'Hard' },
  { quality: 4, label: 'Good' },
  { quality: 5, label: 'Easy' },
] as const

function formatInterval(days: number): string {
  if (days <= 0) return 'later today'
  return days === 1 ? 'in 1 day' : `in ${days} days`
}

function ReviewCard({
  review,
  competency,
  result,
  onSubmitted,
}: {
  review: Review
  competency: CompetencyRef | undefined
  result: Review | undefined
  onSubmitted: (updated: Review) => void
}) {
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
      setError(err instanceof ApiError ? err.message : 'Could not save your answer')
    } finally {
      setPending(null)
    }
  }

  return (
    <Card aria-labelledby={titleId} role="group">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 id={titleId} className="font-medium text-heading">
            {competency?.name ?? `Competency ${review.competency_id.slice(0, 8)}`}
          </h2>
          {competency && (
            <Link
              to={`/subjects/${competency.subjectId}`}
              className="text-sm text-accent-light hover:underline"
            >
              {competency.subjectName}
            </Link>
          )}
        </div>
        <Badge tone={result ? 'success' : 'warning'}>{result ? 'Reviewed' : 'Due'}</Badge>
      </div>

      {result ? (
        <p role="status" className="mt-4 text-sm text-success">
          Saved. Next review {formatInterval(result.interval_days)}.
        </p>
      ) : (
        <fieldset className="mt-4" disabled={pending !== null}>
          <legend className="mb-2 text-sm text-fg-muted">How well did you recall it?</legend>
          <div className="flex flex-wrap gap-2">
            {RECALL_OPTIONS.map((opt) => (
              <Button
                key={opt.quality}
                type="button"
                variant="secondary"
                onClick={() => submit(opt.quality)}
              >
                {opt.quality} · {opt.label}
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
  const { data: index } = useAsync(() => loadCompetencyIndex().catch(() => ({} as Record<string, CompetencyRef>)), [])
  const [results, setResults] = useState<Record<string, Review>>({})

  if (isLoading) return <PageSpinner />
  if (error) return <ErrorAlert message={error} onRetry={refetch} />

  const reviewedCount = data.filter((r) => results[r.id]).length
  const remaining = Math.max(0, list.total - reviewedCount)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-heading">Reviews</h1>
        <p className="mt-1 text-sm text-fg-muted">
          Spaced repetition: rate how well you remember each competency (0 = forgot, 5 = perfect).
        </p>
      </div>

      {data.length === 0 ? (
        <Card>
          <p className="text-sm text-fg-muted">
            Nothing to review right now. Reviews appear here as competencies you studied come due.
          </p>
        </Card>
      ) : (
        <>
          <p className="text-sm text-fg-muted" aria-live="polite">
            {remaining === 0
              ? 'All caught up!'
              : `${remaining} review${remaining === 1 ? '' : 's'} due`}
          </p>
          <div className="space-y-3">
            {data.map((review) => (
              <ReviewCard
                key={review.id}
                review={review}
                competency={index?.[review.competency_id]}
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

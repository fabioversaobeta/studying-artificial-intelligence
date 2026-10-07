import { Link } from 'react-router-dom'
import { useAsync } from '@/hooks/use-async'
import { recommendationService } from '@/services/recommendation-service'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { recommendationHref } from '@/features/recommendations/recommendation-href'
import type { RecommendationKind } from '@/types/api'

const KIND_LABEL: Record<RecommendationKind, string> = {
  review_due: 'Review',
  continue_learning: 'Continue',
  next_in_path: 'Next step',
  take_quiz: 'Quiz',
  goal_deadline: 'Goal',
  strengthen_weak: 'Strengthen',
}

const KIND_CTA: Record<RecommendationKind, string> = {
  review_due: 'Review now',
  continue_learning: 'Keep studying',
  next_in_path: 'Open path',
  take_quiz: 'Take quiz',
  goal_deadline: 'Study now',
  strengthen_weak: 'Practice',
}

export function TodayRecommendationsCard() {
  const { data, error, isLoading, refetch } = useAsync(() => recommendationService.getToday(), [])

  return (
    <Card aria-labelledby="today-recommendations-title" role="region">
      <h2 id="today-recommendations-title" className="mb-3 font-medium text-heading">
        Today&apos;s recommendations
      </h2>
      {isLoading ? (
        <Spinner />
      ) : error ? (
        <ErrorAlert message={error} onRetry={refetch} />
      ) : !data || data.length === 0 ? (
        <p className="text-sm text-fg-muted">
          Nothing to recommend right now.{' '}
          <Link to="/subjects" className="text-accent-light hover:underline">
            Browse subjects
          </Link>
          .
        </p>
      ) : (
        <ul className="space-y-3">
          {data.map((item) => (
            <li
              key={item.competency.id}
              className="flex flex-wrap items-start justify-between gap-2"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-fg">
                  {item.competency.name}{' '}
                  <Badge tone="neutral">{KIND_LABEL[item.kind]}</Badge>
                </p>
                <p className="text-xs text-fg-muted">
                  {item.competency.subject_name} · {item.reason}
                </p>
              </div>
              <Link
                to={recommendationHref(item)}
                aria-label={`${KIND_CTA[item.kind]}: ${item.competency.name}`}
                className="text-sm text-accent-light hover:underline"
              >
                {KIND_CTA[item.kind]} →
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

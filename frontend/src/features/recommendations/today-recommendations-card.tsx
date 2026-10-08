import { Link } from 'react-router-dom'
import { useAsync } from '@/hooks/use-async'
import { recommendationService } from '@/services/recommendation-service'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { recommendationHref } from '@/features/recommendations/recommendation-href'
import { useT } from '@/i18n/use-i18n'

export function TodayRecommendationsCard() {
  const { data, error, isLoading, refetch } = useAsync(() => recommendationService.getToday(), [])
  const t = useT()

  return (
    <Card aria-labelledby="today-recommendations-title" role="region">
      <h2 id="today-recommendations-title" className="mb-3 font-medium text-heading">
        {t('reco.title')}
      </h2>
      {isLoading ? (
        <Spinner />
      ) : error ? (
        <ErrorAlert message={error} onRetry={refetch} />
      ) : !data || data.length === 0 ? (
        <p className="text-sm text-fg-muted">
          {t('reco.empty')}{' '}
          <Link to="/subjects" className="text-accent-light hover:underline">
            {t('reco.browse')}
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
                  <Badge tone="neutral">{t(`reco.kind.${item.kind}`)}</Badge>
                </p>
                <p className="text-xs text-fg-muted">
                  {item.competency.subject_name} · {item.reason}
                </p>
              </div>
              <Link
                to={recommendationHref(item)}
                aria-label={t('reco.ctaLabel', { cta: t(`reco.cta.${item.kind}`), name: item.competency.name })}
                className="text-sm text-accent-light hover:underline"
              >
                {t(`reco.cta.${item.kind}`)} →
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

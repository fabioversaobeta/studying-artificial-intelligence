import { Link, useParams } from 'react-router-dom'
import { useAsync } from '@/hooks/use-async'
import { learningService } from '@/services/learning-service'
import type { CompetencyState, LearningPath } from '@/types/api'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PageSpinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { useT } from '@/i18n/use-i18n'

const sortedItems = (path: LearningPath) =>
  [...path.items].sort((a, b) => a.sort_order - b.sort_order)

const stateTone: Record<CompetencyState, 'neutral' | 'accent' | 'success' | 'warning'> = {
  locked: 'neutral',
  available: 'accent',
  learning: 'warning',
  mastered: 'success',
}

function ProgressBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(Math.min(100, Math.max(0, value)))
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
      className="h-1.5 w-full overflow-hidden rounded-full bg-surface-raised"
    >
      <div className="h-full rounded-full bg-accent" style={{ width: `${pct}%` }} />
    </div>
  )
}

export function LearningPathsPage() {
  const { data, error, isLoading, refetch } = useAsync(() => learningService.listLearningPaths(), [])
  const t = useT()

  if (isLoading) return <PageSpinner />
  if (error) return <ErrorAlert message={error} onRetry={refetch} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-heading">{t('paths.title')}</h1>
        <p className="mt-1 text-sm text-fg-muted">{t('paths.subtitle')}</p>
      </div>

      {data.length === 0 ? (
        <Card>
          <p className="text-sm text-fg-muted">{t('paths.empty')}</p>
        </Card>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2">
          {data.map((path) => (
            <li key={path.id}>
              <Link
                to={`/learning-paths/${path.slug}`}
                className="block rounded-2xl focus-visible:outline-2 focus-visible:outline-accent"
              >
                <Card className="h-full transition-colors hover:border-fg-muted">
                  <h2 className="font-medium text-heading">{path.title}</h2>
                  {path.description && (
                    <p className="mt-1 text-sm text-fg-muted">{path.description}</p>
                  )}
                  <p className="mt-3 text-xs text-fg-muted">
                    {t('paths.steps', { count: path.items.length })}
                    {path.progress &&
                      ` · ${t('paths.masteredSteps', { count: path.progress.mastered_steps })}`}
                  </p>
                  {path.progress && (
                    <div className="mt-2">
                      <ProgressBar
                        label={t('paths.progressLabel', { title: path.title })}
                        value={path.progress.average_mastery}
                      />
                    </div>
                  )}
                </Card>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function LearningPathDetailPage() {
  const { slug } = useParams<{ slug: string }>()
  const { data, error, isLoading, refetch } = useAsync(() => learningService.getLearningPath(slug!), [slug])
  const t = useT()

  if (isLoading) return <PageSpinner />
  if (error) return <ErrorAlert message={error} onRetry={refetch} />
  if (!data) return null

  const items = sortedItems(data)

  return (
    <div className="space-y-6">
      <div>
        <Link to="/learning-paths" className="text-sm text-accent-light hover:underline">
          {t('paths.all')}
        </Link>
        <h1 className="mt-2 text-xl font-semibold text-heading">{data.title}</h1>
        {data.description && <p className="mt-1 text-sm text-fg-muted">{data.description}</p>}
      </div>

      {data.progress && (
        <Card>
          <p className="text-sm text-fg">
            {t('paths.summary', {
              mastered: data.progress.mastered_steps,
              total: data.progress.total_steps,
            })}
            {' · '}
            {t('paths.averageMastery', { value: Math.round(data.progress.average_mastery) })}
          </p>
          <div className="mt-2">
            <ProgressBar label={t('paths.pathProgress')} value={data.progress.average_mastery} />
          </div>
        </Card>
      )}

      {items.length === 0 ? (
        <p className="text-sm text-fg-muted">{t('paths.noSteps')}</p>
      ) : (
        <ol className="space-y-3">
          {items.map((item, i) => (
            <li key={item.competency.id}>
              <Card>
                <div className="flex items-start gap-3">
                  <span
                    className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/15 text-sm font-medium text-accent-light"
                    aria-hidden="true"
                  >
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-medium text-fg">
                        <span className="sr-only">{t('paths.step', { n: i + 1 })}</span>
                        {item.competency.name}
                      </h2>
                      <Badge>{t(`difficulty.${item.competency.difficulty}`)}</Badge>
                      {item.state && (
                        <Badge tone={stateTone[item.state]}>{t(`competency.state.${item.state}`)}</Badge>
                      )}
                    </div>
                    {item.competency.description && (
                      <p className="mt-1 text-sm text-fg-muted">{item.competency.description}</p>
                    )}
                    {item.mastery_score != null && (
                      <div className="mt-2">
                        <ProgressBar
                          label={t('competency.masteryLabel', { name: item.competency.name })}
                          value={item.mastery_score}
                        />
                      </div>
                    )}
                    <Link
                      to={`/subjects/${item.competency.subject_id}`}
                      className="mt-2 inline-block text-sm text-accent-light hover:underline"
                    >
                      {t('paths.studyInSubject')}
                    </Link>
                  </div>
                </div>
              </Card>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}

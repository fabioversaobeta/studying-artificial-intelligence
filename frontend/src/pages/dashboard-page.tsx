import { Link } from 'react-router-dom'
import { useAsync } from '@/hooks/use-async'
import { learningService } from '@/services/learning-service'
import { TodayRecommendationsCard } from '@/features/recommendations/today-recommendations-card'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PageSpinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { useI18n } from '@/i18n/use-i18n'

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <Card>
      <p className="text-xs font-medium uppercase tracking-wide text-fg-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-heading">{value}</p>
      {hint && <p className="mt-1 text-xs text-fg-muted">{hint}</p>}
    </Card>
  )
}

export function DashboardPage() {
  const { data, error, isLoading, refetch } = useAsync(() => learningService.getDashboard(), [])
  const { t, formatDate, formatNumber } = useI18n()

  if (isLoading) return <PageSpinner />
  if (error) return <ErrorAlert message={error} onRetry={refetch} />
  if (!data) return null

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-heading">{t('dashboard.title')}</h1>
        <p className="mt-1 text-sm text-fg-muted">{t('dashboard.subtitle')}</p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label={t('dashboard.level')} value={data.level} hint={t('dashboard.xpToNext', { value: formatNumber(data.xp_to_next_level) })} />
        <StatCard label={t('dashboard.totalXp')} value={formatNumber(data.total_xp)} />
        <StatCard
          label={t('dashboard.streak')}
          value={t('nav.streakShort', { count: data.current_streak_days })}
          hint={t('dashboard.best', { count: data.longest_streak_days })}
        />
        <Link to="/reviews" aria-label={t('dashboard.dueReviewsLink', { count: data.due_review_count })}>
          <StatCard
            label={t('dashboard.dueReviews')}
            value={data.due_review_count}
            hint={data.due_review_count > 0 ? t('dashboard.reviewNow') : undefined}
          />
        </Link>
      </div>

      <TodayRecommendationsCard />

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-medium text-heading">{t('dashboard.activeGoals')}</h2>
            <Link to="/goals" className="text-sm text-accent-light hover:underline">
              {t('dashboard.manage')}
            </Link>
          </div>
          {data.active_goals.length === 0 ? (
            <p className="text-sm text-fg-muted">
              {t('dashboard.noGoals')}{' '}
              <Link to="/goals" className="text-accent-light hover:underline">
                {t('dashboard.setOne')}
              </Link>
              .
            </p>
          ) : (
            <ul className="space-y-2">
              {data.active_goals.map((goal) => (
                <li key={goal.id} className="text-sm text-fg">
                  {goal.title}
                  {goal.target_date && (
                    <span className="ml-2 text-xs text-fg-muted">{t('dashboard.goalBy', { date: formatDate(goal.target_date) })}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <h2 className="mb-3 font-medium text-heading">{t('dashboard.weakest')}</h2>
          {data.weakest_competencies.length === 0 ? (
            <p className="text-sm text-fg-muted">
              {t('dashboard.nothingTracked')}{' '}
              <Link to="/subjects" className="text-accent-light hover:underline">
                {t('dashboard.startStudying')}
              </Link>
              .
            </p>
          ) : (
            <ul className="space-y-2">
              {data.weakest_competencies.map((m) => (
                <li key={m.competency_id} className="flex items-center justify-between text-sm">
                  <span className="text-fg-muted">{t('dashboard.competencyRef', { id: m.competency_id.slice(0, 8) })}</span>
                  <Badge tone={m.score < 40 ? 'danger' : m.score < 80 ? 'warning' : 'success'}>
                    {t('common.percent', { value: formatNumber(m.score, { maximumFractionDigits: 0 }) })}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card>
        <h2 className="mb-3 font-medium text-heading">{t('dashboard.recentSessions')}</h2>
        {data.recent_study_sessions.length === 0 ? (
          <div className="flex items-center justify-between">
            <p className="text-sm text-fg-muted">{t('dashboard.noSessions')}</p>
            <Link to="/subjects">
              <Button variant="secondary">{t('dashboard.browseSubjects')}</Button>
            </Link>
          </div>
        ) : (
          <ul className="space-y-2">
            {data.recent_study_sessions.map((s) => (
              <li key={s.id} className="flex items-center justify-between text-sm">
                <span className="text-fg">{s.notes ?? t('dashboard.studySession')}</span>
                <span className="text-fg-muted">
                  {t('dashboard.sessionMeta', { minutes: s.duration_minutes, date: formatDate(s.occurred_at) })}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}

import { Link } from 'react-router-dom'
import { usePagedList } from '@/hooks/use-paged-list'
import { assessmentService } from '@/services/assessment-service'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { ErrorAlert } from '@/components/ui/alert'
import { LoadMore } from '@/components/ui/load-more'
import { PageSpinner } from '@/components/ui/spinner'
import type { AttemptSummary, CompetencyAssessmentStats } from '@/types/api'
import { useI18n } from '@/i18n/use-i18n'

function StatsSection() {
  const stats = usePagedList((page) => assessmentService.competencyStats(page), 10)
  const { t, formatNumber } = useI18n()
  if (stats.isLoading) return <PageSpinner />
  if (stats.error) return <ErrorAlert message={stats.error} onRetry={stats.reload} />
  if (stats.items.length === 0) return null

  return (
    <section aria-labelledby="quiz-stats-title" className="space-y-3">
      <h2 id="quiz-stats-title" className="text-base font-semibold text-heading">
        {t('history.progressByCompetency')}
      </h2>
      <Card className="overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <caption className="sr-only">{t('history.statsCaption')}</caption>
          <thead className="text-xs text-fg-muted">
            <tr>
              <th scope="col" className="px-4 py-3 font-medium">{t('history.col.competency')}</th>
              <th scope="col" className="px-4 py-3 font-medium">{t('history.col.coverage')}</th>
              <th scope="col" className="px-4 py-3 font-medium">{t('history.col.accuracy')}</th>
              <th scope="col" className="px-4 py-3 font-medium">{t('history.col.attempts')}</th>
              <th scope="col" className="px-4 py-3 font-medium">{t('history.col.xp')}</th>
            </tr>
          </thead>
          <tbody>
            {stats.items.map((row: CompetencyAssessmentStats) => (
              <tr key={row.competency_id} className="border-t border-border">
                <th scope="row" className="px-4 py-3 font-medium text-fg">
                  {row.competency_name}
                  <span className="block text-xs font-normal text-fg-muted">{row.subject_name}</span>
                </th>
                <td className="px-4 py-3 text-fg-muted">
                  {row.questions_correct}/{row.questions_total} ({formatNumber(row.coverage_percent)}%)
                </td>
                <td className="px-4 py-3 text-fg-muted">
                  {row.accuracy_percent === null ? '—' : `${formatNumber(row.accuracy_percent)}%`}
                </td>
                <td className="px-4 py-3 text-fg-muted">{row.attempts_completed}</td>
                <td className="px-4 py-3 text-fg-muted">{formatNumber(row.xp_earned)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
      <LoadMore
        shown={stats.items.length}
        total={stats.total}
        hasMore={stats.hasMore}
        isLoading={stats.isLoadingMore}
        error={stats.loadMoreError}
        onLoadMore={stats.loadMore}
      />
    </section>
  )
}

function AttemptRow({ attempt }: { attempt: AttemptSummary }) {
  const finished = attempt.status === 'completed'
  const { t, formatDateTime, formatNumber } = useI18n()
  return (
    <li>
      <Link
        to={`/quizzes/attempts/${attempt.id}`}
        className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-surface px-5 py-4 hover:border-fg-muted"
      >
        <span>
          <span className="block font-medium text-heading">{attempt.assessment_title}</span>
          <span className="text-xs text-fg-muted">{formatDateTime(attempt.started_at)}</span>
        </span>
        <span className="flex items-center gap-2">
          {finished ? (
            <>
              <span className="text-sm text-fg-muted">
                {attempt.correct_count}/{attempt.total_questions} · {formatNumber(attempt.score_percent ?? 0)}%
              </span>
              <Badge tone={attempt.passed ? 'success' : 'danger'}>
                {attempt.passed ? t('history.passed') : t('history.notPassed')}
              </Badge>
              {attempt.xp_awarded > 0 && <Badge tone="accent">{t('common.xpGain', { value: formatNumber(attempt.xp_awarded) })}</Badge>}
            </>
          ) : (
            <Badge tone="warning">{t('history.inProgress')}</Badge>
          )}
        </span>
      </Link>
    </li>
  )
}

export function QuizHistoryPage() {
  const list = usePagedList((page) => assessmentService.listAttempts(page))
  const { t } = useI18n()

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-heading">{t('history.title')}</h1>
          <p className="mt-1 text-sm text-fg-muted">{t('history.subtitle')}</p>
        </div>
        <Link to="/quizzes" className="text-sm text-accent-light hover:underline">
          {t('history.allQuizzes')}
        </Link>
      </div>

      <StatsSection />

      <section aria-labelledby="quiz-attempts-title" className="space-y-3">
        <h2 id="quiz-attempts-title" className="text-base font-semibold text-heading">
          {t('history.attempts')}
        </h2>
        {list.isLoading ? (
          <PageSpinner />
        ) : list.error ? (
          <ErrorAlert message={list.error} onRetry={list.reload} />
        ) : list.items.length === 0 ? (
          <p className="text-sm text-fg-muted">
            {t('history.noAttempts')}{' '}
            <Link to="/quizzes" className="text-accent-light hover:underline">
              {t('history.takeQuiz')}
            </Link>
            .
          </p>
        ) : (
          <>
            <ul className="space-y-3">
              {list.items.map((attempt) => (
                <AttemptRow key={attempt.id} attempt={attempt} />
              ))}
            </ul>
            <LoadMore
              shown={list.items.length}
              total={list.total}
              hasMore={list.hasMore}
              isLoading={list.isLoadingMore}
              error={list.loadMoreError}
              onLoadMore={list.loadMore}
            />
          </>
        )}
      </section>
    </div>
  )
}

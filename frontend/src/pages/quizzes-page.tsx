import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { usePagedList } from '@/hooks/use-paged-list'
import { assessmentService } from '@/services/assessment-service'
import { useToast } from '@/features/feedback/toast-context'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ErrorAlert } from '@/components/ui/alert'
import { LoadMore } from '@/components/ui/load-more'
import { PageSpinner } from '@/components/ui/spinner'
import type { Assessment } from '@/types/api'
import { useI18n, useT } from '@/i18n/use-i18n'
import type { MessageKey } from '@/i18n'

function actionKey(assessment: Assessment): MessageKey {
  if (assessment.open_attempt_id) return 'quizzes.resume'
  return assessment.attempts_completed > 0 ? 'quizzes.tryAgain' : 'quizzes.start'
}

function AssessmentCard({
  assessment,
  busy,
  onStart,
}: {
  assessment: Assessment
  busy: boolean
  onStart: (assessment: Assessment) => void
}) {
  const titleId = `assessment-${assessment.id}`
  const { t, formatNumber } = useI18n()
  const action = t(actionKey(assessment))
  return (
    <Card role="group" aria-labelledby={titleId} className="space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 id={titleId} className="font-medium text-heading">
            {assessment.title}
          </h2>
          {assessment.competency_name && (
            <p className="text-sm text-accent-light">{assessment.competency_name}</p>
          )}
        </div>
        {assessment.passed ? (
          <Badge tone="success">{t('quizzes.passed')}</Badge>
        ) : assessment.attempts_completed > 0 ? (
          <Badge tone="warning">{t('quizzes.notPassedYet')}</Badge>
        ) : null}
      </div>
      {assessment.description && <p className="text-sm text-fg-muted">{assessment.description}</p>}
      <p className="text-xs text-fg-muted">
        {t('quizzes.meta', {
          questions: assessment.question_count,
          threshold: assessment.pass_threshold,
          bonus: formatNumber(assessment.completion_bonus_xp),
        })}
        {assessment.best_score_percent !== null &&
          t('quizzes.best', { score: assessment.best_score_percent })}
      </p>
      <Button
        type="button"
        onClick={() => onStart(assessment)}
        disabled={busy || assessment.question_count === 0}
        aria-label={t('quizzes.actionLabel', { action, title: assessment.title })}
      >
        {action}
      </Button>
    </Card>
  )
}

export function QuizzesPage() {
  const list = usePagedList((page) => assessmentService.listAssessments(page))
  const navigate = useNavigate()
  const toast = useToast()
  const t = useT()
  const [startingId, setStartingId] = useState<string | null>(null)

  async function start(assessment: Assessment) {
    setStartingId(assessment.id)
    try {
      const attempt = await assessmentService.startAttempt(assessment.id)
      navigate(`/quizzes/attempts/${attempt.id}`)
    } catch (err) {
      toast.showError(err, t('quizzes.startError'))
      setStartingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-heading">{t('quizzes.title')}</h1>
          <p className="mt-1 text-sm text-fg-muted">
            {t('quizzes.subtitle')}
          </p>
        </div>
        <Link to="/quizzes/history" className="text-sm text-accent-light hover:underline">
          {t('quizzes.historyLink')}
        </Link>
      </div>

      {list.isLoading ? (
        <PageSpinner />
      ) : list.error ? (
        <ErrorAlert message={list.error} onRetry={list.reload} />
      ) : list.items.length === 0 ? (
        <p className="text-sm text-fg-muted">{t('quizzes.empty')}</p>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2">
            {list.items.map((assessment) => (
              <AssessmentCard
                key={assessment.id}
                assessment={assessment}
                busy={startingId !== null}
                onStart={(a) => void start(a)}
              />
            ))}
          </div>
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
    </div>
  )
}

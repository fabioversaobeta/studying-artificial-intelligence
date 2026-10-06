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

function actionLabel(assessment: Assessment): string {
  if (assessment.open_attempt_id) return 'Resume'
  return assessment.attempts_completed > 0 ? 'Try again' : 'Start'
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
          <Badge tone="success">Passed</Badge>
        ) : assessment.attempts_completed > 0 ? (
          <Badge tone="warning">Not passed yet</Badge>
        ) : null}
      </div>
      {assessment.description && <p className="text-sm text-fg-muted">{assessment.description}</p>}
      <p className="text-xs text-fg-muted">
        {assessment.question_count} questions · pass at {assessment.pass_threshold}% ·{' '}
        {assessment.completion_bonus_xp} XP bonus on first pass
        {assessment.best_score_percent !== null && ` · best ${assessment.best_score_percent}%`}
      </p>
      <Button
        type="button"
        onClick={() => onStart(assessment)}
        disabled={busy || assessment.question_count === 0}
        aria-label={`${actionLabel(assessment)}: ${assessment.title}`}
      >
        {actionLabel(assessment)}
      </Button>
    </Card>
  )
}

export function QuizzesPage() {
  const list = usePagedList((page) => assessmentService.listAssessments(page))
  const navigate = useNavigate()
  const toast = useToast()
  const [startingId, setStartingId] = useState<string | null>(null)

  async function start(assessment: Assessment) {
    setStartingId(assessment.id)
    try {
      const attempt = await assessmentService.startAttempt(assessment.id)
      navigate(`/quizzes/attempts/${attempt.id}`)
    } catch (err) {
      toast.showError(err, 'Could not start the quiz')
      setStartingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-heading">Quizzes</h1>
          <p className="mt-1 text-sm text-fg-muted">
            Test what you know. XP is earned on the first pass; every attempt still counts for
            mastery.
          </p>
        </div>
        <Link to="/quizzes/history" className="text-sm text-accent-light hover:underline">
          History &amp; stats
        </Link>
      </div>

      {list.isLoading ? (
        <PageSpinner />
      ) : list.error ? (
        <ErrorAlert message={list.error} onRetry={list.reload} />
      ) : list.items.length === 0 ? (
        <p className="text-sm text-fg-muted">No quizzes available yet.</p>
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

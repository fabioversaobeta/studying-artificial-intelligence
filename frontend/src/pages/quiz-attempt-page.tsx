import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAsync } from '@/hooks/use-async'
import { assessmentService } from '@/services/assessment-service'
import { QuizResult } from '@/features/quiz/quiz-result'
import { QuizRunner } from '@/features/quiz/quiz-runner'
import { ErrorAlert } from '@/components/ui/alert'
import { PageSpinner } from '@/components/ui/spinner'
import type { AttemptDetail } from '@/types/api'

/** One attempt: the quiz itself while open, the graded review once finished. */
export function QuizAttemptPage() {
  const { attemptId = '' } = useParams()
  const { data, error, isLoading, refetch } = useAsync(
    () => assessmentService.getAttempt(attemptId),
    [attemptId],
  )
  const [finished, setFinished] = useState<AttemptDetail | null>(null)

  if (isLoading) return <PageSpinner />
  if (error || !data) {
    return (
      <div className="space-y-4">
        <ErrorAlert message={error ?? 'Attempt not found'} onRetry={refetch} />
        <Link to="/quizzes" className="text-sm text-accent-light hover:underline">
          Back to quizzes
        </Link>
      </div>
    )
  }

  const attempt = finished ?? data
  return attempt.status === 'completed' ? (
    <QuizResult attempt={attempt} />
  ) : (
    <QuizRunner key={attempt.id} attempt={attempt} onFinished={setFinished} />
  )
}

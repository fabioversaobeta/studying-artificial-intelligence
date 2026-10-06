import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { assessmentService } from '@/services/assessment-service'
import { ApiError } from '@/services/api-client'
import { LessonContent } from '@/features/learning/lesson-content'
import { InlineMarkdown } from '@/features/quiz/inline-markdown'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ErrorAlert } from '@/components/ui/alert'
import type { AttemptDetail, AttemptQuestion } from '@/types/api'

function verdict(question: AttemptQuestion): { label: string; tone: 'success' | 'danger' | 'neutral' } {
  const correct = question.review?.is_correct
  if (correct === true) return { label: 'Correct', tone: 'success' }
  if (correct === false) {
    return {
      label: question.answer ? 'Incorrect' : 'Not answered',
      tone: 'danger',
    }
  }
  return { label: 'Not graded (counted as wrong)', tone: 'neutral' }
}

function QuestionReviewCard({ question }: { question: AttemptQuestion }) {
  const review = question.review
  const state = verdict(question)
  const selected = new Set(question.answer?.option_ids ?? [])
  const correctIds = new Set(review?.correct_option_ids ?? [])

  return (
    <Card className="space-y-4" role="group" aria-label={`Question ${question.position}`}>
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold text-heading">Question {question.position}</h3>
        <Badge tone={state.tone}>{state.label}</Badge>
        {review && review.xp_awarded > 0 && <Badge tone="accent">+{review.xp_awarded} XP</Badge>}
        {review?.is_first_correct && <Badge>first time correct</Badge>}
      </div>

      <LessonContent markdown={question.prompt} />

      {question.options && (
        <ul className="space-y-2">
          {question.options.map((option) => {
            const isCorrect = correctIds.has(option.id)
            const isSelected = selected.has(option.id)
            return (
              <li
                key={option.id}
                className={[
                  'flex items-start justify-between gap-3 rounded-xl border px-3.5 py-2.5 text-sm',
                  isCorrect ? 'border-success/50 bg-success/10' : 'border-border',
                ].join(' ')}
              >
                <span className="text-fg">
                  <InlineMarkdown>{option.text}</InlineMarkdown>
                </span>
                <span className="flex shrink-0 gap-1.5">
                  {isSelected && <Badge>Your answer</Badge>}
                  {isCorrect && <Badge tone="success">Correct answer</Badge>}
                </span>
              </li>
            )
          })}
        </ul>
      )}

      {!question.options && (
        <div className="space-y-2 text-sm">
          <div>
            <h4 className="font-medium text-fg-subtle">Your answer</h4>
            <p className="whitespace-pre-wrap text-fg">{question.answer?.text ?? 'No answer'}</p>
          </div>
          {review?.model_answer && (
            <div>
              <h4 className="font-medium text-fg-subtle">Model answer</h4>
              <p className="text-fg">
                <InlineMarkdown>{review.model_answer}</InlineMarkdown>
              </p>
            </div>
          )}
        </div>
      )}

      {review && (
        <div className="rounded-xl bg-surface-raised p-3 text-sm">
          <h4 className="mb-1 font-medium text-heading">Explanation</h4>
          <p className="text-fg-muted">
            <InlineMarkdown>{review.explanation}</InlineMarkdown>
          </p>
        </div>
      )}
    </Card>
  )
}

export function QuizResult({ attempt }: { attempt: AttemptDetail }) {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const passed = attempt.passed === true

  async function tryAgain() {
    setBusy(true)
    setError(null)
    try {
      const next = await assessmentService.startAttempt(attempt.assessment_id)
      navigate(`/quizzes/attempts/${next.id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not start a new attempt')
      setBusy(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card className="space-y-4" aria-labelledby="quiz-result-title">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 id="quiz-result-title" className="text-lg font-semibold text-heading">
            {attempt.assessment_title}
          </h1>
          <Badge tone={passed ? 'success' : 'danger'}>{passed ? 'Passed' : 'Not passed'}</Badge>
        </div>

        <p className="text-3xl font-semibold text-heading">
          {attempt.score_percent ?? 0}%
          <span className="ml-3 text-sm font-normal text-fg-muted">
            {attempt.correct_count ?? 0} of {attempt.total_questions} correct · pass mark{' '}
            {attempt.pass_threshold}%
          </span>
        </p>

        <div role="status" className="space-y-1 text-sm">
          {attempt.xp_awarded > 0 ? (
            <p className="text-success">
              +{attempt.xp_awarded} XP earned ({attempt.xp_questions} from questions
              {attempt.xp_bonus > 0 ? `, ${attempt.xp_bonus} completion bonus` : ''}).
            </p>
          ) : passed ? (
            <p className="text-fg-muted">
              No new XP: every question you got right had already earned its XP. It still counts
              for your mastery and streak.
            </p>
          ) : (
            <p className="text-fg-muted">
              XP is only awarded when you reach the pass mark. This attempt still counts for your
              mastery and streak.
            </p>
          )}
          {attempt.pending_review_count > 0 && (
            <p className="text-warning">
              {attempt.pending_review_count} short answer
              {attempt.pending_review_count === 1 ? ' was' : 's were'} not self-graded and counted
              as wrong.
            </p>
          )}
        </div>

        {error && <ErrorAlert message={error} />}

        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={() => void tryAgain()} disabled={busy}>
            Try again
          </Button>
          <Link
            to="/quizzes"
            className="inline-flex items-center rounded-full border border-border px-4 py-2 text-sm font-medium text-fg hover:border-fg-muted"
          >
            Back to quizzes
          </Link>
          <Link
            to="/quizzes/history"
            className="inline-flex items-center rounded-full px-4 py-2 text-sm font-medium text-fg-muted hover:text-fg"
          >
            History
          </Link>
        </div>
      </Card>

      <section aria-labelledby="quiz-review-title" className="space-y-3">
        <h2 id="quiz-review-title" className="text-base font-semibold text-heading">
          Review
        </h2>
        {attempt.questions.map((question) => (
          <QuestionReviewCard key={question.id} question={question} />
        ))}
      </section>
    </div>
  )
}

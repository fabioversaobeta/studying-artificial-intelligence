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
import { useI18n } from '@/i18n/use-i18n'
import type { MessageKey } from '@/i18n'

function verdict(question: AttemptQuestion): { label: MessageKey; tone: 'success' | 'danger' | 'neutral' } {
  const correct = question.review?.is_correct
  if (correct === true) return { label: 'result.correct', tone: 'success' }
  if (correct === false) {
    return {
      label: question.answer ? 'result.incorrect' : 'result.notAnswered',
      tone: 'danger',
    }
  }
  return { label: 'result.notGraded', tone: 'neutral' }
}

function QuestionReviewCard({ question }: { question: AttemptQuestion }) {
  const review = question.review
  const state = verdict(question)
  const { t, formatNumber } = useI18n()
  const selected = new Set(question.answer?.option_ids ?? [])
  const correctIds = new Set(review?.correct_option_ids ?? [])

  return (
    <Card className="space-y-4" role="group" aria-label={t('quiz.questionLabel', { n: question.position })}>
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold text-heading">{t('quiz.questionLabel', { n: question.position })}</h3>
        <Badge tone={state.tone}>{t(state.label)}</Badge>
        {review && review.xp_awarded > 0 && <Badge tone="accent">{t('common.xpGain', { value: formatNumber(review.xp_awarded) })}</Badge>}
        {review?.is_first_correct && <Badge>{t('result.firstCorrect')}</Badge>}
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
                  {isSelected && <Badge>{t('result.yourAnswerBadge')}</Badge>}
                  {isCorrect && <Badge tone="success">{t('result.correctAnswerBadge')}</Badge>}
                </span>
              </li>
            )
          })}
        </ul>
      )}

      {!question.options && (
        <div className="space-y-2 text-sm">
          <div>
            <h4 className="font-medium text-fg-subtle">{t('quiz.yourAnswerLabel')}</h4>
            <p className="whitespace-pre-wrap text-fg">{question.answer?.text ?? t('result.noAnswer')}</p>
          </div>
          {review?.model_answer && (
            <div>
              <h4 className="font-medium text-fg-subtle">{t('quiz.modelAnswer')}</h4>
              <p className="text-fg">
                <InlineMarkdown>{review.model_answer}</InlineMarkdown>
              </p>
            </div>
          )}
        </div>
      )}

      {review && (
        <div className="rounded-xl bg-surface-raised p-3 text-sm">
          <h4 className="mb-1 font-medium text-heading">{t('result.explanation')}</h4>
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
  const { t, formatNumber } = useI18n()
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
      setError(err instanceof ApiError ? err.message : t('result.newAttemptError'))
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
          <Badge tone={passed ? 'success' : 'danger'}>{passed ? t('result.passed') : t('result.notPassed')}</Badge>
        </div>

        <p className="text-3xl font-semibold text-heading">
          {formatNumber(attempt.score_percent ?? 0)}%
          <span className="ml-3 text-sm font-normal text-fg-muted">
            {t('result.scoreDetail', {
              correct: attempt.correct_count ?? 0,
              total: attempt.total_questions,
              threshold: attempt.pass_threshold,
            })}
          </span>
        </p>

        <div role="status" className="space-y-1 text-sm">
          {attempt.xp_awarded > 0 ? (
            <p className="text-success">
              {t('result.xpEarned', {
                xp: formatNumber(attempt.xp_awarded),
                questions: formatNumber(attempt.xp_questions),
                bonus:
                  attempt.xp_bonus > 0
                    ? t('result.xpBonus', { bonus: formatNumber(attempt.xp_bonus) })
                    : '',
              })}
            </p>
          ) : passed ? (
            <p className="text-fg-muted">
              {t('result.noNewXp')}
            </p>
          ) : (
            <p className="text-fg-muted">
              {t('result.noXpFailed')}
            </p>
          )}
          {attempt.pending_review_count > 0 && (
            <p className="text-warning">
              {t('result.pending', { count: attempt.pending_review_count })}
            </p>
          )}
        </div>

        {error && <ErrorAlert message={error} />}

        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={() => void tryAgain()} disabled={busy}>
            {t('result.tryAgain')}
          </Button>
          <Link
            to="/quizzes"
            className="inline-flex items-center rounded-full border border-border px-4 py-2 text-sm font-medium text-fg hover:border-fg-muted"
          >
            {t('result.backToQuizzes')}
          </Link>
          <Link
            to="/quizzes/history"
            className="inline-flex items-center rounded-full px-4 py-2 text-sm font-medium text-fg-muted hover:text-fg"
          >
            {t('result.history')}
          </Link>
        </div>
      </Card>

      <section aria-labelledby="quiz-review-title" className="space-y-3">
        <h2 id="quiz-review-title" className="text-base font-semibold text-heading">
          {t('result.review')}
        </h2>
        {attempt.questions.map((question) => (
          <QuestionReviewCard key={question.id} question={question} />
        ))}
      </section>
    </div>
  )
}

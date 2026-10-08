import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { assessmentService } from '@/services/assessment-service'
import { ApiError } from '@/services/api-client'
import { LessonContent } from '@/features/learning/lesson-content'
import { InlineMarkdown } from '@/features/quiz/inline-markdown'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ErrorAlert } from '@/components/ui/alert'
import { Textarea } from '@/components/ui/input'
import type { AnswerResult, AttemptDetail, AttemptQuestion } from '@/types/api'
import { useI18n } from '@/i18n/use-i18n'

interface Draft {
  optionIds: string[]
  text: string
}

const difficultyTone = { easy: 'success', medium: 'warning', hard: 'danger' } as const

function initialDrafts(questions: AttemptQuestion[]): Record<string, Draft> {
  const drafts: Record<string, Draft> = {}
  for (const q of questions) {
    drafts[q.id] = { optionIds: q.answer?.option_ids ?? [], text: q.answer?.text ?? '' }
  }
  return drafts
}

function hasAnswer(question: AttemptQuestion, draft: Draft | undefined): boolean {
  if (!draft) return false
  return question.type === 'short_answer' ? draft.text.trim() !== '' : draft.optionIds.length > 0
}

function isDirty(question: AttemptQuestion, draft: Draft): boolean {
  if (question.type === 'short_answer') {
    return draft.text.trim() !== (question.answer?.text ?? '')
  }
  const saved = [...(question.answer?.option_ids ?? [])].sort().join('|')
  return [...draft.optionIds].sort().join('|') !== saved
}

function messageOf(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback
}

export function QuizRunner({
  attempt,
  onFinished,
}: {
  attempt: AttemptDetail
  onFinished: (result: AttemptDetail) => void
}) {
  const { t, formatNumber } = useI18n()
  const [questions, setQuestions] = useState(attempt.questions)
  const [drafts, setDrafts] = useState(() => initialDrafts(attempt.questions))
  const [index, setIndex] = useState(() => {
    const firstOpen = attempt.questions.findIndex((q) => !q.answer)
    return firstOpen === -1 ? 0 : firstOpen
  })
  const [reveals, setReveals] = useState<Record<string, AnswerResult>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmFinish, setConfirmFinish] = useState(false)
  const headingRef = useRef<HTMLHeadingElement>(null)
  const shownAt = useRef(Date.now())

  const total = questions.length
  const question = questions[index]
  const draft = drafts[question.id] ?? { optionIds: [], text: '' }
  const isLast = index === total - 1
  const answeredCount = questions.filter((q) => hasAnswer(q, drafts[q.id])).length
  const unanswered = total - answeredCount

  // Moving to another question moves focus to its heading, so screen readers
  // announce "Question N of M" and keyboard users start from the top.
  useEffect(() => {
    headingRef.current?.focus()
    shownAt.current = Date.now()
  }, [index])

  function setDraft(next: Partial<Draft>) {
    setDrafts((prev) => ({ ...prev, [question.id]: { ...draft, ...next } }))
    setConfirmFinish(false)
  }

  function chooseOption(optionId: string) {
    if (question.type === 'multi_select') {
      const selected = draft.optionIds.includes(optionId)
      setDraft({
        optionIds: selected
          ? draft.optionIds.filter((id) => id !== optionId)
          : [...draft.optionIds, optionId],
      })
    } else {
      setDraft({ optionIds: [optionId] })
    }
  }

  /** Saves the current question's answer if it changed. Returns false on failure. */
  async function persist(force = false): Promise<boolean> {
    if (!hasAnswer(question, draft)) return true
    if (!force && !isDirty(question, draft)) return true
    setError(null)
    try {
      const seconds = Math.min(86_400, Math.round((Date.now() - shownAt.current) / 1000))
      const result = await assessmentService.saveAnswer(
        attempt.id,
        question.id,
        question.type === 'short_answer'
          ? { text: draft.text.trim(), time_spent_seconds: seconds }
          : { option_ids: draft.optionIds, time_spent_seconds: seconds },
      )
      setQuestions((prev) =>
        prev.map((q) =>
          q.id === question.id
            ? {
                ...q,
                answer: {
                  option_ids: question.type === 'short_answer' ? null : draft.optionIds,
                  text: question.type === 'short_answer' ? draft.text.trim() : null,
                  grading_status: result.grading_status,
                  time_spent_seconds: seconds,
                },
              }
            : q,
        ),
      )
      if (question.type === 'short_answer') {
        setReveals((prev) => ({ ...prev, [question.id]: result }))
      }
      return true
    } catch (err) {
      setError(messageOf(err, t('quiz.saveError')))
      return false
    }
  }

  async function go(target: number) {
    if (busy || target < 0 || target >= total) return
    setBusy(true)
    if (await persist()) setIndex(target)
    setBusy(false)
  }

  async function checkShortAnswer() {
    setBusy(true)
    await persist(true)
    setBusy(false)
  }

  async function selfGrade(isCorrect: boolean) {
    setBusy(true)
    setError(null)
    try {
      const result = await assessmentService.selfGrade(attempt.id, question.id, isCorrect)
      setReveals((prev) => ({ ...prev, [question.id]: result }))
    } catch (err) {
      setError(messageOf(err, t('quiz.gradeError')))
    } finally {
      setBusy(false)
    }
  }

  async function finish(force = false) {
    if (busy) return
    if (unanswered > 0 && !force && !confirmFinish) {
      setConfirmFinish(true)
      return
    }
    setBusy(true)
    try {
      if (!(await persist())) return
      onFinished(await assessmentService.finishAttempt(attempt.id))
    } catch (err) {
      setError(messageOf(err, t('quiz.finishError')))
    } finally {
      setBusy(false)
    }
  }

  function onKeyDown(e: KeyboardEvent<HTMLDivElement>) {
    const target = e.target as HTMLElement
    const isTextField =
      target.tagName === 'TEXTAREA' ||
      (target.tagName === 'INPUT' && (target as HTMLInputElement).type === 'text')
    if (isTextField) return
    if (e.ctrlKey || e.metaKey || e.altKey) return

    if (/^[1-9]$/.test(e.key) && question.options) {
      const option = question.options[Number(e.key) - 1]
      if (option) {
        e.preventDefault()
        chooseOption(option.id)
      }
    } else if (e.key === 'n' || e.key === 'N' || (e.key === 'Enter' && target.tagName !== 'BUTTON')) {
      e.preventDefault()
      if (isLast) void finish()
      else void go(index + 1)
    } else if (e.key === 'p' || e.key === 'P') {
      e.preventDefault()
      void go(index - 1)
    }
  }

  const reveal = reveals[question.id]
  const isShort = question.type === 'short_answer'
  const savedShort = isShort && question.answer && !isDirty(question, draft)
  const fieldsetName = `question-${question.id}`

  return (
    <div className="space-y-5" onKeyDown={onKeyDown}>
      <header className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-lg font-semibold text-heading">{attempt.assessment_title}</h1>
          <p className="text-sm text-fg-muted" aria-live="polite">
            {t('quiz.answeredCount', { answered: answeredCount, total })}
          </p>
        </div>
        <div
          role="progressbar"
          aria-label={t('quiz.answeredProgress')}
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={answeredCount}
          className="h-2 overflow-hidden rounded-full bg-surface-raised"
        >
          <div
            className="h-full bg-accent transition-all"
            style={{ width: `${(answeredCount / total) * 100}%` }}
          />
        </div>
        <nav aria-label={t('quiz.questionsNav')} className="flex flex-wrap gap-1.5">
          {questions.map((q, i) => {
            const answered = hasAnswer(q, drafts[q.id])
            return (
              <button
                key={q.id}
                type="button"
                onClick={() => void go(i)}
                disabled={busy}
                aria-label={t(answered ? 'quiz.questionNavAnswered' : 'quiz.questionNavUnanswered', { n: i + 1 })}
                aria-current={i === index ? 'step' : undefined}
                className={[
                  'h-8 w-8 rounded-full text-sm font-medium transition-colors',
                  i === index
                    ? 'bg-accent text-bg'
                    : answered
                      ? 'bg-accent/20 text-accent-light'
                      : 'border border-border text-fg-muted hover:text-fg',
                ].join(' ')}
              >
                {i + 1}
              </button>
            )
          })}
        </nav>
      </header>

      <Card className="space-y-5">
        <div className="flex flex-wrap items-center gap-2">
          <h2
            ref={headingRef}
            tabIndex={-1}
            className="text-sm font-semibold text-heading focus:outline-none"
          >
            {t('quiz.questionHeading', { n: index + 1, total })}
          </h2>
          <Badge tone={difficultyTone[question.difficulty]}>{t(`difficulty.${question.difficulty}`)}</Badge>
          <Badge tone="accent">{t('common.xp', { value: formatNumber(question.xp_value) })}</Badge>
          {question.type === 'multi_select' && <Badge>{t('quiz.selectAll')}</Badge>}
          {question.type === 'short_answer' && <Badge>{t('quiz.shortAnswer')}</Badge>}
        </div>

        <LessonContent markdown={question.prompt} />

        {question.options ? (
          <fieldset className="space-y-2" disabled={busy}>
            <legend className="sr-only">
              {question.type === 'multi_select' ? t('quiz.legendMulti') : t('quiz.legendSingle')}
            </legend>
            {question.options.map((option, i) => {
              const checked = draft.optionIds.includes(option.id)
              return (
                <label
                  key={option.id}
                  className={[
                    'flex cursor-pointer items-start gap-3 rounded-xl border px-3.5 py-3 text-sm',
                    'focus-within:ring-2 focus-within:ring-accent',
                    checked ? 'border-accent bg-accent/10' : 'border-border hover:border-fg-muted',
                  ].join(' ')}
                >
                  <input
                    type={question.type === 'multi_select' ? 'checkbox' : 'radio'}
                    name={fieldsetName}
                    value={option.id}
                    checked={checked}
                    onChange={() => chooseOption(option.id)}
                    className="mt-0.5 accent-[var(--color-accent)]"
                  />
                  <span className="flex-1 text-fg">
                    <InlineMarkdown>{option.text}</InlineMarkdown>
                  </span>
                  {i < 9 && (
                    <kbd
                      aria-hidden="true"
                      className="rounded border border-border px-1.5 text-xs text-fg-muted"
                    >
                      {i + 1}
                    </kbd>
                  )}
                </label>
              )
            })}
          </fieldset>
        ) : (
          <div className="space-y-3">
            <div>
              <label htmlFor={`${fieldsetName}-text`} className="sr-only">
                {t('quiz.yourAnswerLabel')}
              </label>
              <Textarea
                id={`${fieldsetName}-text`}
                rows={5}
                maxLength={5000}
                placeholder={t('quiz.answerPlaceholder')}
                value={draft.text}
                disabled={busy}
                onChange={(e) => setDraft({ text: e.target.value })}
              />
            </div>
            {!reveal && (
              <Button
                type="button"
                variant="secondary"
                disabled={busy || draft.text.trim() === ''}
                onClick={() => void checkShortAnswer()}
              >
                {t('quiz.checkAnswer')}
              </Button>
            )}
            {savedShort && reveal && (
              <div className="space-y-3 rounded-xl border border-border bg-surface-raised p-4">
                <h3 className="text-sm font-semibold text-heading">{t('quiz.modelAnswer')}</h3>
                <p className="text-sm text-fg">
                  <InlineMarkdown>{reveal.model_answer ?? ''}</InlineMarkdown>
                </p>
                {reveal.explanation && (
                  <p className="text-sm text-fg-muted">
                    <InlineMarkdown>{reveal.explanation}</InlineMarkdown>
                  </p>
                )}
                <div role="group" aria-label={t('quiz.gradeGroup')} className="flex gap-2">
                  <Button
                    type="button"
                    variant={reveal.is_correct === true ? 'primary' : 'secondary'}
                    aria-pressed={reveal.is_correct === true}
                    disabled={busy}
                    onClick={() => void selfGrade(true)}
                  >
                    {t('quiz.gotRight')}
                  </Button>
                  <Button
                    type="button"
                    variant={reveal.is_correct === false ? 'primary' : 'secondary'}
                    aria-pressed={reveal.is_correct === false}
                    disabled={busy}
                    onClick={() => void selfGrade(false)}
                  >
                    {t('quiz.gotWrong')}
                  </Button>
                </div>
                <p className="text-xs text-fg-muted">
                  {t('quiz.selfGradeNote')}
                </p>
              </div>
            )}
          </div>
        )}
      </Card>

      {error && <ErrorAlert message={error} />}

      {confirmFinish && (
        <div
          role="alertdialog"
          aria-label={t('quiz.finishDialog')}
          className="space-y-3 rounded-2xl border border-warning/40 bg-warning/10 p-4 text-sm"
        >
          <p className="text-fg">
            {t('quiz.unanswered', { count: unanswered })}
          </p>
          <div className="flex gap-2">
            <Button type="button" onClick={() => void finish(true)} disabled={busy}>
              {t('quiz.finishAnyway')}
            </Button>
            <Button type="button" variant="ghost" onClick={() => setConfirmFinish(false)}>
              {t('quiz.keepAnswering')}
            </Button>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between gap-3">
        <Button
          type="button"
          variant="secondary"
          disabled={busy || index === 0}
          onClick={() => void go(index - 1)}
        >
          {t('quiz.previous')}
        </Button>
        {isLast ? (
          <Button type="button" disabled={busy} onClick={() => void finish()}>
            {busy ? t('quiz.saving') : t('quiz.finish')}
          </Button>
        ) : (
          <Button type="button" disabled={busy} onClick={() => void go(index + 1)}>
            {t('quiz.next')}
          </Button>
        )}
      </div>
      <p className="text-xs text-fg-muted">
        {t('quiz.kbdIntro')} <kbd>1</kbd>–<kbd>9</kbd> {t('quiz.kbdChoose')} <kbd>N</kbd>{' '}
        {t('quiz.kbdOr')} <kbd>Enter</kbd> {t('quiz.kbdNext')} <kbd>P</kbd> {t('quiz.kbdPrevious')}
      </p>
    </div>
  )
}

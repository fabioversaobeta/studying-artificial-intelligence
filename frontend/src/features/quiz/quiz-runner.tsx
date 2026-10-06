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
      setError(messageOf(err, 'Could not save your answer'))
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
      setError(messageOf(err, 'Could not save your grade'))
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
      setError(messageOf(err, 'Could not finish the quiz'))
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
            {answeredCount} of {total} answered
          </p>
        </div>
        <div
          role="progressbar"
          aria-label="Questions answered"
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
        <nav aria-label="Questions" className="flex flex-wrap gap-1.5">
          {questions.map((q, i) => {
            const answered = hasAnswer(q, drafts[q.id])
            return (
              <button
                key={q.id}
                type="button"
                onClick={() => void go(i)}
                disabled={busy}
                aria-label={`Question ${i + 1}${answered ? ', answered' : ', not answered'}`}
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
            Question {index + 1} of {total}
          </h2>
          <Badge tone={difficultyTone[question.difficulty]}>{question.difficulty}</Badge>
          <Badge tone="accent">{question.xp_value} XP</Badge>
          {question.type === 'multi_select' && <Badge>select all that apply</Badge>}
          {question.type === 'short_answer' && <Badge>short answer</Badge>}
        </div>

        <LessonContent markdown={question.prompt} />

        {question.options ? (
          <fieldset className="space-y-2" disabled={busy}>
            <legend className="sr-only">
              {question.type === 'multi_select' ? 'Select all that apply' : 'Choose one answer'}
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
                Your answer
              </label>
              <Textarea
                id={`${fieldsetName}-text`}
                rows={5}
                maxLength={5000}
                placeholder="Write your answer in your own words…"
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
                Check answer
              </Button>
            )}
            {savedShort && reveal && (
              <div className="space-y-3 rounded-xl border border-border bg-surface-raised p-4">
                <h3 className="text-sm font-semibold text-heading">Model answer</h3>
                <p className="text-sm text-fg">
                  <InlineMarkdown>{reveal.model_answer ?? ''}</InlineMarkdown>
                </p>
                {reveal.explanation && (
                  <p className="text-sm text-fg-muted">
                    <InlineMarkdown>{reveal.explanation}</InlineMarkdown>
                  </p>
                )}
                <div role="group" aria-label="Grade your own answer" className="flex gap-2">
                  <Button
                    type="button"
                    variant={reveal.is_correct === true ? 'primary' : 'secondary'}
                    aria-pressed={reveal.is_correct === true}
                    disabled={busy}
                    onClick={() => void selfGrade(true)}
                  >
                    I got it right
                  </Button>
                  <Button
                    type="button"
                    variant={reveal.is_correct === false ? 'primary' : 'secondary'}
                    aria-pressed={reveal.is_correct === false}
                    disabled={busy}
                    onClick={() => void selfGrade(false)}
                  >
                    I got it wrong
                  </Button>
                </div>
                <p className="text-xs text-fg-muted">
                  You grade this one yourself. Ungraded short answers count as wrong.
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
          aria-label="Finish with unanswered questions"
          className="space-y-3 rounded-2xl border border-warning/40 bg-warning/10 p-4 text-sm"
        >
          <p className="text-fg">
            {unanswered === 1
              ? '1 question is unanswered and will count as wrong.'
              : `${unanswered} questions are unanswered and will count as wrong.`}
          </p>
          <div className="flex gap-2">
            <Button type="button" onClick={() => void finish(true)} disabled={busy}>
              Finish anyway
            </Button>
            <Button type="button" variant="ghost" onClick={() => setConfirmFinish(false)}>
              Keep answering
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
          Previous
        </Button>
        {isLast ? (
          <Button type="button" disabled={busy} onClick={() => void finish()}>
            {busy ? 'Saving…' : 'Finish quiz'}
          </Button>
        ) : (
          <Button type="button" disabled={busy} onClick={() => void go(index + 1)}>
            Next
          </Button>
        )}
      </div>
      <p className="text-xs text-fg-muted">
        Keyboard: <kbd>1</kbd>–<kbd>9</kbd> choose an option, <kbd>N</kbd> or <kbd>Enter</kbd> next,{' '}
        <kbd>P</kbd> previous.
      </p>
    </div>
  )
}

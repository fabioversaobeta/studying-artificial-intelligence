import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QuizAttemptPage } from '@/pages/quiz-attempt-page'
import { assessmentService } from '@/services/assessment-service'
import { ApiError } from '@/services/api-client'
import { makeAttempt, makeQuestion, makeReview } from '@/test/quiz-fixtures'

vi.mock('@/services/assessment-service', () => ({
  assessmentService: {
    getAttempt: vi.fn(),
    saveAnswer: vi.fn(),
    selfGrade: vi.fn(),
    finishAttempt: vi.fn(),
    startAttempt: vi.fn(),
  },
}))

const svc = vi.mocked(assessmentService)

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/quizzes/attempts/attempt-1']}>
      <Routes>
        <Route path="/quizzes/attempts/:attemptId" element={<QuizAttemptPage />} />
        <Route path="/quizzes" element={<p>quizzes list</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

const saved = { question_id: 'q1', saved: true, grading_status: 'graded' as const }
const answerResult = {
  ...saved,
  model_answer: null,
  explanation: null,
  is_correct: null,
}

beforeEach(() => {
  vi.resetAllMocks()
  svc.saveAnswer.mockResolvedValue(answerResult)
})

describe('QuizAttemptPage (in progress)', () => {
  it('shows one question at a time with progress and an accessible question list', async () => {
    svc.getAttempt.mockResolvedValue(makeAttempt())
    renderPage()

    const heading = await screen.findByRole('heading', { name: 'Question 1 of 3' })
    // Focus is applied in a passive effect that can flush after findByRole resolves.
    await waitFor(() => expect(heading).toHaveFocus())
    expect(screen.getByText('Prompt 1')).toBeInTheDocument()
    expect(screen.queryByText('Prompt 2')).not.toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: 'Questions answered' })).toHaveAttribute(
      'aria-valuenow',
      '0',
    )
    expect(screen.getByRole('button', { name: 'Question 1, not answered' })).toHaveAttribute(
      'aria-current',
      'step',
    )
    expect(screen.getByRole('radio', { name: /Q1 option A/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled()
  })

  it('never renders answer material while the quiz is open', async () => {
    svc.getAttempt.mockResolvedValue(makeAttempt())
    renderPage()
    await screen.findByText('Prompt 1')
    expect(screen.queryByText(/Correct answer/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Explanation/)).not.toBeInTheDocument()
  })

  it('saves the chosen option when moving to the next question', async () => {
    svc.getAttempt.mockResolvedValue(makeAttempt())
    renderPage()
    await userEvent.click(await screen.findByRole('radio', { name: /Q1 option B/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))

    const next = await screen.findByRole('heading', { name: 'Question 2 of 3' })
    await waitFor(() => expect(next).toHaveFocus())
    expect(svc.saveAnswer).toHaveBeenCalledWith('attempt-1', 'q1', {
      option_ids: ['b'],
      time_spent_seconds: expect.any(Number),
    })
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '1')
    expect(screen.getByRole('button', { name: 'Question 1, answered' })).toBeInTheDocument()
  })

  it('does not call the API for questions left blank or unchanged', async () => {
    svc.getAttempt.mockResolvedValue(makeAttempt())
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: 'Next' }))
    await screen.findByRole('heading', { name: 'Question 2 of 3' })
    expect(svc.saveAnswer).not.toHaveBeenCalled()
  })

  it('supports the keyboard: digits choose, N next, P previous', async () => {
    svc.getAttempt.mockResolvedValue(makeAttempt())
    renderPage()
    await screen.findByRole('heading', { name: 'Question 1 of 3' })

    await userEvent.keyboard('2')
    expect(screen.getByRole('radio', { name: /Q1 option B/ })).toBeChecked()
    await userEvent.keyboard('n')
    const next = await screen.findByRole('heading', { name: 'Question 2 of 3' })
    await waitFor(() => expect(next).toHaveFocus())
    expect(svc.saveAnswer).toHaveBeenCalledWith('attempt-1', 'q1', expect.objectContaining({
      option_ids: ['b'],
    }))
    await userEvent.keyboard('p')
    expect(await screen.findByRole('heading', { name: 'Question 1 of 3' })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /Q1 option B/ })).toBeChecked()
  })

  it('does not hijack typing inside the short-answer field', async () => {
    svc.getAttempt.mockResolvedValue(
      makeAttempt({
        questions: [makeQuestion(1, { type: 'short_answer', options: null }), makeQuestion(2)],
      }),
    )
    renderPage()
    const field = await screen.findByLabelText('Your answer')
    await userEvent.type(field, 'pen 1 name')
    expect(field).toHaveValue('pen 1 name')
    expect(screen.getByRole('heading', { name: 'Question 1 of 2' })).toBeInTheDocument()
  })

  it('lets multi-select questions toggle several options', async () => {
    svc.getAttempt.mockResolvedValue(
      makeAttempt({ questions: [makeQuestion(1, { type: 'multi_select' })] }),
    )
    renderPage()
    await userEvent.click(await screen.findByRole('checkbox', { name: /Q1 option A/ }))
    await userEvent.click(screen.getByRole('checkbox', { name: /Q1 option C/ }))
    await userEvent.click(screen.getByRole('checkbox', { name: /Q1 option A/ }))
    expect(screen.getByRole('checkbox', { name: /Q1 option A/ })).not.toBeChecked()
    expect(screen.getByRole('checkbox', { name: /Q1 option C/ })).toBeChecked()
    expect(screen.getByText('select all that apply')).toBeInTheDocument()
  })

  it('restores saved answers and jumps to the first unanswered question', async () => {
    const answered = makeQuestion(1, {
      answer: {
        option_ids: ['b'],
        text: null,
        grading_status: 'graded',
        time_spent_seconds: 3,
      },
    })
    svc.getAttempt.mockResolvedValue(makeAttempt({ questions: [answered, makeQuestion(2)] }))
    renderPage()
    expect(await screen.findByRole('heading', { name: 'Question 2 of 2' })).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '1')
  })

  it('keeps you on the question and shows the error when saving fails', async () => {
    svc.getAttempt.mockResolvedValue(makeAttempt())
    svc.saveAnswer.mockRejectedValue(new ApiError('conflict', 'This attempt is already finished', 409))
    renderPage()
    await userEvent.click(await screen.findByRole('radio', { name: /Q1 option A/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('already finished')
    expect(screen.getByRole('heading', { name: 'Question 1 of 3' })).toBeInTheDocument()
  })

  it('asks for confirmation before finishing with unanswered questions', async () => {
    svc.getAttempt.mockResolvedValue(makeAttempt({ questions: [makeQuestion(1), makeQuestion(2)] }))
    renderPage()
    await userEvent.click(await screen.findByRole('radio', { name: /Q1 option B/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Finish quiz' }))

    const dialog = screen.getByRole('alertdialog')
    expect(dialog).toHaveTextContent('1 question is unanswered')
    expect(svc.finishAttempt).not.toHaveBeenCalled()

    await userEvent.click(within(dialog).getByRole('button', { name: 'Keep answering' }))
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  })

  it('finishes and shows the graded review with explanations and XP', async () => {
    svc.getAttempt.mockResolvedValue(makeAttempt({ questions: [makeQuestion(1)] }))
    svc.finishAttempt.mockResolvedValue(
      makeAttempt({
        status: 'completed',
        passed: true,
        correct_count: 1,
        score_percent: 100,
        xp_awarded: 35,
        xp_questions: 10,
        xp_bonus: 25,
        questions: [
          makeQuestion(1, {
            answer: {
              option_ids: ['b'],
              text: null,
              grading_status: 'graded',
              time_spent_seconds: 2,
            },
            review: makeReview(),
          }),
        ],
      }),
    )
    renderPage()
    await userEvent.click(await screen.findByRole('radio', { name: /Q1 option B/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Finish quiz' }))

    expect(await screen.findByText('Passed')).toBeInTheDocument()
    expect(screen.getByText(/100%/)).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('+35 XP earned (10 from questions, 25 completion bonus)')
    expect(screen.getByText('Because B is right.')).toBeInTheDocument()
    expect(screen.getByText('Correct answer')).toBeInTheDocument()
    expect(screen.getByText('Your answer')).toBeInTheDocument()
    expect(screen.getByText('first time correct')).toBeInTheDocument()
    expect(svc.saveAnswer).toHaveBeenCalledWith('attempt-1', 'q1', expect.objectContaining({
      option_ids: ['b'],
    }))
  })

  it('walks through a short answer: check, read the model answer, self-grade', async () => {
    svc.getAttempt.mockResolvedValue(
      makeAttempt({ questions: [makeQuestion(1, { type: 'short_answer', options: null })] }),
    )
    svc.saveAnswer.mockResolvedValue({
      question_id: 'q1',
      saved: true,
      grading_status: 'pending_review',
      model_answer: 'The reference answer.',
      explanation: 'Compare yours.',
      is_correct: null,
    })
    svc.selfGrade.mockResolvedValue({
      question_id: 'q1',
      saved: true,
      grading_status: 'self_graded',
      model_answer: 'The reference answer.',
      explanation: 'Compare yours.',
      is_correct: true,
    })
    renderPage()
    await userEvent.type(await screen.findByLabelText('Your answer'), 'my own words')
    expect(screen.queryByText('The reference answer.')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Check answer' }))

    expect(await screen.findByText('The reference answer.')).toBeInTheDocument()
    expect(svc.saveAnswer).toHaveBeenCalledWith('attempt-1', 'q1', {
      text: 'my own words',
      time_spent_seconds: expect.any(Number),
    })
    await userEvent.click(screen.getByRole('button', { name: 'I got it right' }))
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'I got it right' })).toHaveAttribute(
        'aria-pressed',
        'true',
      ),
    )
    expect(svc.selfGrade).toHaveBeenCalledWith('attempt-1', 'q1', true)
  })
})

describe('QuizAttemptPage (finished / errors)', () => {
  const finished = makeAttempt({
    status: 'completed',
    passed: false,
    correct_count: 1,
    score_percent: 33.33,
    xp_awarded: 0,
    pending_review_count: 1,
    questions: [
      makeQuestion(1, {
        answer: { option_ids: ['a'], text: null, grading_status: 'graded', time_spent_seconds: 1 },
        review: makeReview({ is_correct: false, xp_awarded: 0, is_first_correct: false }),
      }),
      makeQuestion(2, {
        type: 'short_answer',
        options: null,
        answer: {
          option_ids: null,
          text: 'my text',
          grading_status: 'pending_review',
          time_spent_seconds: 1,
        },
        review: makeReview({
          correct_option_ids: null,
          model_answer: 'Reference.',
          is_correct: null,
          grading_status: 'pending_review',
          xp_awarded: 0,
          is_first_correct: false,
        }),
      }),
    ],
  })

  it('opens a finished attempt directly on its review', async () => {
    svc.getAttempt.mockResolvedValue(finished)
    renderPage()
    expect(await screen.findByText('Not passed')).toBeInTheDocument()
    expect(screen.getByText(/XP is only awarded when you reach the pass mark/)).toBeInTheDocument()
    expect(screen.getByText(/1 short answer was not self-graded/)).toBeInTheDocument()
    expect(screen.getByText('Incorrect')).toBeInTheDocument()
    expect(screen.getByText('Not graded (counted as wrong)')).toBeInTheDocument()
    expect(screen.getByText('Reference.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Finish quiz' })).not.toBeInTheDocument()
  })

  it('explains a pass that earned no new XP', async () => {
    svc.getAttempt.mockResolvedValue({ ...finished, passed: true, xp_awarded: 0 })
    renderPage()
    expect(await screen.findByText(/every question you got right had already earned/)).toBeInTheDocument()
  })

  it('starts a new attempt from "Try again"', async () => {
    svc.getAttempt.mockResolvedValue(finished)
    svc.startAttempt.mockResolvedValue(makeAttempt({ id: 'attempt-2' }))
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: 'Try again' }))
    expect(svc.startAttempt).toHaveBeenCalledWith('assessment-1')
  })

  it('shows an error with a way back when the attempt cannot be loaded', async () => {
    svc.getAttempt.mockRejectedValue(new ApiError('not_found', 'Attempt not found', 404))
    renderPage()
    expect(await screen.findByText('Attempt not found')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back to quizzes' })).toHaveAttribute('href', '/quizzes')
  })
})

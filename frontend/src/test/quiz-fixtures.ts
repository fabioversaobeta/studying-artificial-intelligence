import type { AttemptDetail, AttemptQuestion, QuestionReview } from '@/types/api'

export function makeQuestion(
  position: number,
  overrides: Partial<AttemptQuestion> = {},
): AttemptQuestion {
  return {
    id: `q${position}`,
    position,
    type: 'multiple_choice',
    difficulty: 'easy',
    xp_value: 10,
    tags: [],
    prompt: `Prompt ${position}`,
    options: [
      { id: 'a', text: `Q${position} option A` },
      { id: 'b', text: `Q${position} option B` },
      { id: 'c', text: `Q${position} option C` },
    ],
    language: 'en',
    answer: null,
    review: null,
    ...overrides,
  }
}

export function makeAttempt(overrides: Partial<AttemptDetail> = {}): AttemptDetail {
  const questions = overrides.questions ?? [makeQuestion(1), makeQuestion(2), makeQuestion(3)]
  return {
    id: 'attempt-1',
    assessment_id: 'assessment-1',
    assessment_title: 'Type Hints Quiz',
    status: 'in_progress',
    started_at: '2026-01-01T10:00:00Z',
    completed_at: null,
    total_questions: questions.length,
    correct_count: null,
    score_percent: null,
    passed: null,
    xp_awarded: 0,
    pass_threshold: 70,
    answered_count: 0,
    xp_questions: 0,
    xp_bonus: 0,
    pending_review_count: 0,
    questions,
    ...overrides,
  }
}

export function makeReview(overrides: Partial<QuestionReview> = {}): QuestionReview {
  return {
    correct_option_ids: ['b'],
    explanation: 'Because B is right.',
    model_answer: null,
    is_correct: true,
    grading_status: 'graded',
    xp_awarded: 10,
    is_first_correct: true,
    ...overrides,
  }
}

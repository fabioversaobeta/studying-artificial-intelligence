import { apiClient, type PageParams } from '@/services/api-client'
import type {
  AnswerResult,
  Assessment,
  AttemptDetail,
  AttemptSummary,
  CompetencyAssessmentStats,
} from '@/types/api'

/** Quizzes. The content language comes from the user's preference (see Settings). */
export const assessmentService = {
  listAssessments: (params?: PageParams & { competencyId?: string }) => {
    const { competencyId, ...page } = params ?? {}
    const path = competencyId
      ? `/api/v1/assessments?competency_id=${encodeURIComponent(competencyId)}`
      : '/api/v1/assessments'
    return apiClient.getPaged<Assessment>(path, page)
  },

  /** Starts a new attempt, or resumes the open one for that assessment. */
  startAttempt: (assessmentId: string) =>
    apiClient.post<AttemptDetail>(`/api/v1/assessments/${assessmentId}/attempts`),

  getAttempt: (attemptId: string) => apiClient.get<AttemptDetail>(`/api/v1/attempts/${attemptId}`),

  listAttempts: (params?: PageParams) =>
    apiClient.getPaged<AttemptSummary>('/api/v1/attempts', params),

  saveAnswer: (
    attemptId: string,
    questionId: string,
    answer: { option_ids?: string[]; text?: string; time_spent_seconds?: number },
  ) =>
    apiClient.patch<AnswerResult>(`/api/v1/attempts/${attemptId}/responses/${questionId}`, answer),

  selfGrade: (attemptId: string, questionId: string, isCorrect: boolean) =>
    apiClient.post<AnswerResult>(
      `/api/v1/attempts/${attemptId}/responses/${questionId}/self-grade`,
      { is_correct: isCorrect },
    ),

  finishAttempt: (attemptId: string) =>
    apiClient.post<AttemptDetail>(`/api/v1/attempts/${attemptId}/finish`),

  competencyStats: (params?: PageParams) =>
    apiClient.getPaged<CompetencyAssessmentStats>('/api/v1/assessments/stats/by-competency', params),
}

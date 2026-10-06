import { apiClient, type PageParams } from '@/services/api-client'
import type {
  Challenge,
  ChallengeSubmission,
  ChallengeSubmissionStatus,
  Dashboard,
  LearningGoal,
  LearningPath,
  LearningResource,
  GoalStatus,
  Review,
  StudySession,
  SubjectDetail,
  SubjectWithProgress,
} from '@/types/api'

export const learningService = {
  getDashboard: () => apiClient.get<Dashboard>('/api/v1/dashboard'),

  listSubjects: () => apiClient.get<SubjectWithProgress[]>('/api/v1/subjects'),
  getSubject: (id: string) => apiClient.get<SubjectDetail>(`/api/v1/subjects/${id}`),

  listLearningPaths: () => apiClient.get<LearningPath[]>('/api/v1/learning-paths'),
  getLearningPath: (slug: string) =>
    apiClient.get<LearningPath>(`/api/v1/learning-paths/${encodeURIComponent(slug)}`),

  logStudySession: (input: {
    competency_id?: string
    subject_id?: string
    duration_minutes: number
    notes?: string
  }) => apiClient.post<StudySession>('/api/v1/study-sessions', input),
  listStudySessions: (params?: PageParams) =>
    apiClient.getPaged<StudySession>('/api/v1/study-sessions', params),

  listGoals: (params?: PageParams) => apiClient.getPaged<LearningGoal>('/api/v1/goals', params),
  createGoal: (input: { title: string; description?: string; target_date?: string }) =>
    apiClient.post<LearningGoal>('/api/v1/goals', input),
  updateGoalStatus: (goalId: string, status: GoalStatus) =>
    apiClient.patch<LearningGoal>(`/api/v1/goals/${goalId}/status`, { status }),

  listResources: (competencyId: string) =>
    apiClient.get<LearningResource[]>(`/api/v1/competencies/${competencyId}/resources`),

  listChallenges: (competencyId: string) =>
    apiClient.get<Challenge[]>(`/api/v1/competencies/${competencyId}/challenges`),
  submitChallenge: (challengeId: string, status: ChallengeSubmissionStatus, notes?: string) =>
    apiClient.post<ChallengeSubmission>(`/api/v1/challenges/${challengeId}/submissions`, {
      status,
      notes,
    }),

  listDueReviews: (params?: PageParams) =>
    apiClient.getPaged<Review>('/api/v1/reviews/due', params),
  submitRecall: (competencyId: string, quality: number) =>
    apiClient.post<Review>(`/api/v1/reviews/${competencyId}/recall`, { quality }),
}

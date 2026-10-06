// Mirrors backend/app/schemas/*.py. Keep in sync manually — see docs/API.md.

export type Uuid = string

export interface User {
  id: Uuid
  email: string
  display_name: string
  is_active: boolean
}

export interface RegistrationInfo {
  enabled: boolean
  invite_required: boolean
}

// The refresh token is never in the body: it is an HttpOnly cookie.
export interface TokenResponse {
  access_token: string
  token_type: string
}

export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced'
export type ResourceType =
  | 'lesson'
  | 'article'
  | 'book'
  | 'video'
  | 'documentation'
  | 'course'
  | 'notes'
export type GoalStatus = 'active' | 'achieved' | 'archived'
export type ChallengeSubmissionStatus = 'submitted' | 'passed' | 'failed'
export type CompetencyState = 'locked' | 'available' | 'learning' | 'mastered'

export interface Subject {
  id: Uuid
  name: string
  slug: string
  description: string | null
  icon: string | null
  color: string | null
  sort_order: number
}

export interface SubjectWithProgress {
  subject: Subject
  competency_count: number
  average_mastery: number
}

export interface Competency {
  id: Uuid
  subject_id: Uuid
  name: string
  slug: string
  description: string | null
  difficulty: DifficultyLevel
  sort_order: number
}

export interface CompetencyWithState {
  competency: Competency
  mastery_score: number
  state: CompetencyState
}

export interface SubjectDetail {
  subject: Subject
  competencies: CompetencyWithState[]
}

export interface LearningResource {
  id: Uuid
  type: ResourceType
  title: string
  url: string | null
  description: string | null
  content: string | null
}

export interface LearningPathItem {
  competency: Competency
  sort_order: number
  /** Per-user progress; null/absent when the request was anonymous. */
  mastery_score?: number | null
  state?: CompetencyState | null
}

export interface LearningPathProgress {
  total_steps: number
  mastered_steps: number
  average_mastery: number
}

export interface LearningPath {
  id: Uuid
  title: string
  slug: string
  description: string | null
  items: LearningPathItem[]
  progress?: LearningPathProgress | null
}

export interface StudySession {
  id: Uuid
  competency_id: Uuid | null
  subject_id: Uuid | null
  duration_minutes: number
  notes: string | null
  occurred_at: string
}

export interface LearningGoal {
  id: Uuid
  title: string
  description: string | null
  status: GoalStatus
  target_date: string | null
  created_at: string
}

export interface Challenge {
  id: Uuid
  competency_id: Uuid
  title: string
  description: string
  difficulty: DifficultyLevel
  xp_value: number
}

export interface ChallengeSubmission {
  id: Uuid
  challenge_id: Uuid
  status: ChallengeSubmissionStatus
  notes: string | null
  submitted_at: string
  xp_awarded: number
}

export interface Review {
  id: Uuid
  competency_id: Uuid
  interval_days: number
  ease_factor: number
  repetitions: number
  due_at: string
  last_reviewed_at: string | null
  last_recall_quality: number | null
}

export interface DueReview extends Review {
  competency_name: string
  subject_id: Uuid
  subject_name: string
}

export interface MasteryRecord {
  competency_id: Uuid
  score: number
  updated_at: string
}

export interface GamificationProfile {
  total_xp: number
  level: number
  current_streak_days: number
  longest_streak_days: number
  last_activity_date: string | null
}

export interface Achievement {
  id: Uuid
  code: string
  name: string
  description: string
  icon: string | null
  criteria_type: string
  criteria_value: number | null
  xp_reward: number
}

export interface AchievementProgress {
  achievement: Achievement
  earned: boolean
  earned_at: string | null
}

export interface Quest {
  id: Uuid
  code: string
  title: string
  description: string
  criteria_type: string
  criteria_value: number
  period: 'one_time' | 'weekly'
  xp_reward: number
}

export interface QuestProgress {
  quest: Quest
  progress: number
  target: number
  completed: boolean
  period_key: string
}

export interface Dashboard {
  level: number
  total_xp: number
  xp_to_next_level: number
  current_streak_days: number
  longest_streak_days: number
  active_goals: LearningGoal[]
  due_review_count: number
  weakest_competencies: MasteryRecord[]
  recent_study_sessions: StudySession[]
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
  }
}

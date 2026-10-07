// Mirrors backend/app/schemas/*.py. Keep in sync manually — see docs/API.md.

export type Uuid = string

export type Language = 'en' | 'pt-BR'

export interface User {
  id: Uuid
  email: string
  display_name: string
  preferred_language: Language
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

// ---- Recommendations ("what to study today") -------------------------------

export type RecommendationKind =
  | 'review_due'
  | 'continue_learning'
  | 'next_in_path'
  | 'take_quiz'
  | 'goal_deadline'
  | 'strengthen_weak'

export interface RecommendationAction {
  type: 'review' | 'competency' | 'assessment' | 'path'
  id: Uuid | null
  slug: string | null
}

export interface Recommendation {
  kind: RecommendationKind
  competency: { id: Uuid; name: string; subject_id: Uuid; subject_name: string }
  reason: string
  score: number
  action: RecommendationAction
}

// ---- Assessments (quizzes) -------------------------------------------------

export type QuestionType = 'multiple_choice' | 'multi_select' | 'short_answer' | 'code_reading'
export type QuestionDifficulty = 'easy' | 'medium' | 'hard'
export type AttemptStatus = 'in_progress' | 'completed'
export type GradingStatus = 'graded' | 'pending_review' | 'self_graded'

export interface Assessment {
  id: Uuid
  code: string
  title: string
  description: string | null
  kind: 'competency' | 'learning_path' | 'mixed'
  competency_id: Uuid | null
  competency_name: string | null
  pass_threshold: number
  completion_bonus_xp: number
  question_count: number
  attempts_completed: number
  best_score_percent: number | null
  passed: boolean
  open_attempt_id: Uuid | null
}

export interface QuizOption {
  id: string
  text: string
}

export interface SavedAnswer {
  option_ids: string[] | null
  text: string | null
  grading_status: GradingStatus
  time_spent_seconds: number | null
}

/** Present only on finished attempts. */
export interface QuestionReview {
  correct_option_ids: string[] | null
  explanation: string
  model_answer: string | null
  is_correct: boolean | null
  grading_status: GradingStatus
  xp_awarded: number
  is_first_correct: boolean
}

export interface AttemptQuestion {
  id: Uuid
  position: number
  type: QuestionType
  difficulty: QuestionDifficulty
  xp_value: number
  tags: string[]
  prompt: string
  options: QuizOption[] | null
  language: Language
  answer: SavedAnswer | null
  review: QuestionReview | null
}

export interface AttemptSummary {
  id: Uuid
  assessment_id: Uuid
  assessment_title: string
  status: AttemptStatus
  started_at: string
  completed_at: string | null
  total_questions: number
  correct_count: number | null
  score_percent: number | null
  passed: boolean | null
  xp_awarded: number
}

export interface AttemptDetail extends AttemptSummary {
  pass_threshold: number
  answered_count: number
  xp_questions: number
  xp_bonus: number
  pending_review_count: number
  questions: AttemptQuestion[]
}

export interface AnswerResult {
  question_id: Uuid
  saved: boolean
  grading_status: GradingStatus
  model_answer: string | null
  explanation: string | null
  is_correct: boolean | null
}

export interface CompetencyAssessmentStats {
  competency_id: Uuid
  competency_name: string
  subject_name: string
  questions_total: number
  questions_answered: number
  questions_correct: number
  coverage_percent: number
  attempts_completed: number
  responses_graded: number
  responses_correct: number
  accuracy_percent: number | null
  xp_earned: number
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
  }
}

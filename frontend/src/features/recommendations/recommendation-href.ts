import type { Recommendation } from '@/types/api'

/** Where a suggestion leads (routes of the existing pages). */
export function recommendationHref(item: Recommendation): string {
  const { action, competency } = item
  switch (action.type) {
    case 'review':
      return '/reviews'
    case 'assessment':
      return '/quizzes'
    case 'path':
      return `/learning-paths/${encodeURIComponent(action.slug ?? '')}`
    default:
      return `/subjects/${competency.subject_id}`
  }
}

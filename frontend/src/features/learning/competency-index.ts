import { learningService } from '@/services/learning-service'

export interface CompetencyRef {
  name: string
  subjectId: string
  subjectName: string
}

/**
 * Builds a competency-id -> {name, subject} lookup from the subjects API.
 * Reviews only carry a competency id, so screens that list them need this to
 * show something readable. Best-effort: subjects that fail to load are skipped.
 */
export async function loadCompetencyIndex(): Promise<Record<string, CompetencyRef>> {
  const subjects = await learningService.listSubjects()
  const details = await Promise.allSettled(
    subjects.map((s) => learningService.getSubject(s.subject.id)),
  )
  const index: Record<string, CompetencyRef> = {}
  for (const result of details) {
    if (result.status !== 'fulfilled') continue
    const { subject, competencies } = result.value
    for (const { competency } of competencies) {
      index[competency.id] = {
        name: competency.name,
        subjectId: subject.id,
        subjectName: subject.name,
      }
    }
  }
  return index
}

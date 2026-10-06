import { Link, useParams } from 'react-router-dom'
import { useAsync } from '@/hooks/use-async'
import { learningService } from '@/services/learning-service'
import { PageSpinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { CompetencyCard } from '@/features/learning/competency-card'

export function SubjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data, error, isLoading, refetch } = useAsync(
    () => learningService.getSubject(id!),
    [id],
  )

  if (isLoading) return <PageSpinner />
  if (error) return <ErrorAlert message={error} onRetry={refetch} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <div>
        <Link to="/subjects" className="text-sm text-accent-light hover:underline">
          ← All subjects
        </Link>
        <h1 className="mt-2 text-xl font-semibold text-heading">{data.subject.name}</h1>
        <p className="mt-1 text-sm text-fg-muted">{data.subject.description}</p>
      </div>

      <div className="space-y-3">
        {data.competencies.map((item) => (
          <CompetencyCard key={item.competency.id} item={item} onActivity={refetch} />
        ))}
      </div>
    </div>
  )
}

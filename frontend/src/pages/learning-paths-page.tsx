import { Link, useParams } from 'react-router-dom'
import { useAsync } from '@/hooks/use-async'
import { learningService } from '@/services/learning-service'
import type { LearningPath } from '@/types/api'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PageSpinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'

const sortedItems = (path: LearningPath) =>
  [...path.items].sort((a, b) => a.sort_order - b.sort_order)

export function LearningPathsPage() {
  const { data, error, isLoading } = useAsync(() => learningService.listLearningPaths(), [])

  if (isLoading) return <PageSpinner />
  if (error) return <ErrorAlert message={error} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-heading">Learning Paths</h1>
        <p className="mt-1 text-sm text-fg-muted">Curated sequences of competencies to follow.</p>
      </div>

      {data.length === 0 ? (
        <Card>
          <p className="text-sm text-fg-muted">No learning paths available yet.</p>
        </Card>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2">
          {data.map((path) => (
            <li key={path.id}>
              <Link
                to={`/learning-paths/${path.slug}`}
                className="block rounded-2xl focus-visible:outline-2 focus-visible:outline-accent"
              >
                <Card className="h-full transition-colors hover:border-fg-muted">
                  <h2 className="font-medium text-heading">{path.title}</h2>
                  {path.description && (
                    <p className="mt-1 text-sm text-fg-muted">{path.description}</p>
                  )}
                  <p className="mt-3 text-xs text-fg-muted">
                    {path.items.length} step{path.items.length === 1 ? '' : 's'}
                  </p>
                </Card>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function LearningPathDetailPage() {
  const { slug } = useParams<{ slug: string }>()
  const { data, error, isLoading } = useAsync(() => learningService.getLearningPath(slug!), [slug])

  if (isLoading) return <PageSpinner />
  if (error) return <ErrorAlert message={error} />
  if (!data) return null

  const items = sortedItems(data)

  return (
    <div className="space-y-6">
      <div>
        <Link to="/learning-paths" className="text-sm text-accent-light hover:underline">
          ← All learning paths
        </Link>
        <h1 className="mt-2 text-xl font-semibold text-heading">{data.title}</h1>
        {data.description && <p className="mt-1 text-sm text-fg-muted">{data.description}</p>}
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-fg-muted">This path has no steps yet.</p>
      ) : (
        <ol className="space-y-3">
          {items.map((item, i) => (
            <li key={item.competency.id}>
              <Card>
                <div className="flex items-start gap-3">
                  <span
                    className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/15 text-sm font-medium text-accent-light"
                    aria-hidden="true"
                  >
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-medium text-fg">
                        <span className="sr-only">Step {i + 1}: </span>
                        {item.competency.name}
                      </h2>
                      <Badge>{item.competency.difficulty}</Badge>
                    </div>
                    {item.competency.description && (
                      <p className="mt-1 text-sm text-fg-muted">{item.competency.description}</p>
                    )}
                    <Link
                      to={`/subjects/${item.competency.subject_id}`}
                      className="mt-2 inline-block text-sm text-accent-light hover:underline"
                    >
                      Study in subject →
                    </Link>
                  </div>
                </div>
              </Card>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}

import { useState } from 'react'
import { useAsync } from '@/hooks/use-async'
import { learningService } from '@/services/learning-service'
import { Spinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { LessonContent } from '@/features/learning/lesson-content'
import type { LearningResource } from '@/types/api'

const EXTERNAL_TYPE_LABEL: Record<string, string> = {
  article: 'Article',
  book: 'Book',
  video: 'Video',
  documentation: 'Documentation',
  course: 'Course',
  notes: 'Notes',
}

function LessonModule({ resource, defaultOpen }: { resource: LearningResource; defaultOpen: boolean }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="rounded-xl border border-border">
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
      >
        <span className="text-sm font-medium text-fg">{resource.title}</span>
        <span className="text-xs text-fg-muted">{isOpen ? 'Hide' : 'Read'}</span>
      </button>
      {isOpen && resource.content && (
        <div className="border-t border-border px-4 py-4">
          <LessonContent markdown={resource.content} />
        </div>
      )}
    </div>
  )
}

function ExternalResourceLink({ resource }: { resource: LearningResource }) {
  return (
    <li className="flex items-center justify-between gap-3 text-sm">
      <span className="text-fg-muted">
        <span className="mr-2 rounded bg-surface-raised px-1.5 py-0.5 text-xs uppercase tracking-wide">
          {EXTERNAL_TYPE_LABEL[resource.type] ?? resource.type}
        </span>
        {resource.title}
      </span>
      {resource.url && (
        <a
          href={resource.url}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 text-accent-light hover:underline"
        >
          Open ↗
        </a>
      )}
    </li>
  )
}

export function ResourceList({ competencyId }: { competencyId: string }) {
  const { data: resources, error, isLoading } = useAsync(
    () => learningService.listResources(competencyId),
    [competencyId],
  )

  if (isLoading) return <Spinner />
  if (error) return <ErrorAlert message={error} />
  if (!resources || resources.length === 0) {
    return <p className="text-sm text-fg-muted">No study material for this competency yet.</p>
  }

  const lessons = resources.filter((r) => r.type === 'lesson')
  const external = resources.filter((r) => r.type !== 'lesson')

  return (
    <div className="space-y-4">
      {lessons.length > 0 && (
        <div className="space-y-2">
          {lessons.map((resource, index) => (
            <LessonModule key={resource.id} resource={resource} defaultOpen={index === 0} />
          ))}
        </div>
      )}
      {external.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-fg-muted">
            Further reading
          </h4>
          <ul className="space-y-2">
            {external.map((resource) => (
              <ExternalResourceLink key={resource.id} resource={resource} />
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import { useAsync } from '@/hooks/use-async'
import { learningService } from '@/services/learning-service'
import { Spinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { LessonContent } from '@/features/learning/lesson-content'
import type { LearningResource } from '@/types/api'
import { useT } from '@/i18n/use-i18n'

const EXTERNAL_TYPES = ['article', 'book', 'video', 'documentation', 'course', 'notes'] as const

function LessonModule({ resource, defaultOpen }: { resource: LearningResource; defaultOpen: boolean }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const t = useT()

  return (
    <div className="rounded-xl border border-border">
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        aria-expanded={isOpen}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
      >
        <span className="text-sm font-medium text-fg">{resource.title}</span>
        <span className="text-xs text-fg-muted">{isOpen ? t('resources.hide') : t('resources.read')}</span>
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
  const t = useT()
  const knownType = EXTERNAL_TYPES.find((type) => type === resource.type)
  return (
    <li className="flex items-center justify-between gap-3 text-sm">
      <span className="text-fg-muted">
        <span className="mr-2 rounded bg-surface-raised px-1.5 py-0.5 text-xs uppercase tracking-wide">
          {knownType ? t(`resources.type.${knownType}`) : resource.type}
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
          {t('resources.open')}
        </a>
      )}
    </li>
  )
}

export function ResourceList({ competencyId }: { competencyId: string }) {
  const t = useT()
  const { data: resources, error, isLoading } = useAsync(
    () => learningService.listResources(competencyId),
    [competencyId],
  )

  if (isLoading) return <Spinner />
  if (error) return <ErrorAlert message={error} />
  if (!resources || resources.length === 0) {
    return <p className="text-sm text-fg-muted">{t('resources.none')}</p>
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
            {t('resources.furtherReading')}
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

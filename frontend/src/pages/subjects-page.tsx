import { Link } from 'react-router-dom'
import { useAsync } from '@/hooks/use-async'
import { learningService } from '@/services/learning-service'
import { Card } from '@/components/ui/card'
import { PageSpinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { useI18n } from '@/i18n/use-i18n'

export function SubjectsPage() {
  const { data: subjects, error, isLoading, refetch } = useAsync(() => learningService.listSubjects(), [])
  const { t, formatNumber } = useI18n()

  if (isLoading) return <PageSpinner />
  if (error) return <ErrorAlert message={error} onRetry={refetch} />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-heading">{t('subjects.title')}</h1>
        <p className="mt-1 text-sm text-fg-muted">{t('subjects.subtitle')}</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {subjects?.map(({ subject, competency_count, average_mastery }) => (
          <Link key={subject.id} to={`/subjects/${subject.id}`}>
            <Card className="h-full transition-colors hover:border-fg-muted">
              <div className="flex items-center justify-between">
                <h2 className="font-medium text-heading">{subject.name}</h2>
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: subject.color ?? '#6685FF' }}
                />
              </div>
              <p className="mt-2 line-clamp-2 text-sm text-fg-muted">{subject.description}</p>
              <div className="mt-4 flex items-center justify-between text-xs text-fg-muted">
                <span>{t('subjects.competencies', { count: competency_count })}</span>
                <span>{t('subjects.mastery', { value: formatNumber(average_mastery, { maximumFractionDigits: 0 }) })}</span>
              </div>
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surface-raised">
                <div
                  className="h-full rounded-full bg-accent"
                  style={{ width: `${Math.min(100, average_mastery)}%` }}
                />
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}

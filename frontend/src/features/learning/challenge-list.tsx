import { useState } from 'react'
import { useAsync } from '@/hooks/use-async'
import { learningService } from '@/services/learning-service'
import { ApiError } from '@/services/api-client'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { useI18n } from '@/i18n/use-i18n'

export function ChallengeList({
  competencyId,
  onActivity,
}: {
  competencyId: string
  onActivity: () => void
}) {
  const { t, formatNumber } = useI18n()
  const { data: challenges, error, isLoading, refetch } = useAsync(
    () => learningService.listChallenges(competencyId),
    [competencyId],
  )
  const [submittingId, setSubmittingId] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [xpToast, setXpToast] = useState<string | null>(null)

  async function submit(challengeId: string, status: 'passed' | 'failed') {
    setSubmittingId(challengeId)
    setSubmitError(null)
    try {
      const result = await learningService.submitChallenge(challengeId, status)
      if (result.xp_awarded > 0) {
        setXpToast(t('common.xpGain', { value: formatNumber(result.xp_awarded) }))
        setTimeout(() => setXpToast(null), 3000)
      }
      refetch()
      onActivity()
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t('challenges.submitError'))
    } finally {
      setSubmittingId(null)
    }
  }

  if (isLoading) return <Spinner />
  if (error) return <ErrorAlert message={error} />
  if (!challenges || challenges.length === 0) {
    return <p className="text-sm text-fg-muted">{t('challenges.none')}</p>
  }

  return (
    <div className="space-y-3">
      {submitError && <ErrorAlert message={submitError} />}
      {xpToast && <Badge tone="success">{xpToast}</Badge>}
      {challenges.map((challenge) => (
        <div key={challenge.id} className="rounded-xl border border-border p-3">
          <div className="flex items-center justify-between gap-3">
            <h4 className="text-sm font-medium text-fg">{challenge.title}</h4>
            <Badge tone="accent">{t('common.xp', { value: formatNumber(challenge.xp_value) })}</Badge>
          </div>
          <p className="mt-1 text-sm text-fg-muted">{challenge.description}</p>
          <div className="mt-3 flex gap-2">
            <Button
              variant="secondary"
              disabled={submittingId === challenge.id}
              onClick={() => submit(challenge.id, 'passed')}
            >
              {t('challenges.markPassed')}
            </Button>
            <Button
              variant="ghost"
              disabled={submittingId === challenge.id}
              onClick={() => submit(challenge.id, 'failed')}
            >
              {t('challenges.markFailed')}
            </Button>
          </div>
        </div>
      ))}
    </div>
  )
}

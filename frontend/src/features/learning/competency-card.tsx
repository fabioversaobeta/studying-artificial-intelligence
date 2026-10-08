import { useState } from 'react'
import clsx from 'clsx'
import type { CompetencyWithState } from '@/types/api'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LogSessionForm } from '@/features/learning/log-session-form'
import { ChallengeList } from '@/features/learning/challenge-list'
import { ResourceList } from '@/features/learning/resource-list'
import { useI18n } from '@/i18n/use-i18n'

const stateTone: Record<CompetencyWithState['state'], 'neutral' | 'accent' | 'success' | 'warning'> = {
  locked: 'neutral',
  available: 'accent',
  learning: 'warning',
  mastered: 'success',
}

export function CompetencyCard({
  item,
  onActivity,
}: {
  item: CompetencyWithState
  onActivity: () => void
}) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { t, formatNumber } = useI18n()
  const { competency, mastery_score, state } = item
  const isLocked = state === 'locked'

  return (
    <Card className={clsx(isLocked && 'opacity-60')}>
      <button
        type="button"
        onClick={() => !isLocked && setIsExpanded((v) => !v)}
        disabled={isLocked}
        aria-expanded={isLocked ? undefined : isExpanded}
        className="flex w-full items-center justify-between gap-3 text-left disabled:cursor-not-allowed"
      >
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-fg">{competency.name}</h3>
            <Badge tone={stateTone[state]}>{t(`competency.state.${state}`)}</Badge>
          </div>
          <p className="mt-1 text-sm text-fg-muted">{competency.description}</p>
        </div>
        <div className="shrink-0 text-right">
          <span className="text-sm font-medium text-fg">{t('common.percent', { value: formatNumber(mastery_score, { maximumFractionDigits: 0 }) })}</span>
        </div>
      </button>

      <div
        role="progressbar"
        aria-label={t('competency.masteryLabel', { name: competency.name })}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(Math.min(100, mastery_score))}
        className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-surface-raised"
      >
        <div
          className="h-full rounded-full bg-accent"
          style={{ width: `${Math.min(100, mastery_score)}%` }}
        />
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-6 border-t border-border pt-4">
          <div>
            <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-fg-muted">
              {t('competency.study')}
            </h4>
            <ResourceList competencyId={competency.id} />
          </div>

          <div>
            <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-fg-muted">
              {t('competency.logSession')}
            </h4>
            <LogSessionForm competencyId={competency.id} onLogged={onActivity} />
          </div>

          <div>
            <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-fg-muted">
              {t('competency.challenges')}
            </h4>
            <ChallengeList competencyId={competency.id} onActivity={onActivity} />
          </div>
        </div>
      )}
    </Card>
  )
}

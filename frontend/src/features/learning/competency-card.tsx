import { useState } from 'react'
import clsx from 'clsx'
import type { CompetencyWithState } from '@/types/api'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { LogSessionForm } from '@/features/learning/log-session-form'
import { ChallengeList } from '@/features/learning/challenge-list'

const stateTone: Record<CompetencyWithState['state'], 'neutral' | 'accent' | 'success' | 'warning'> = {
  locked: 'neutral',
  available: 'accent',
  learning: 'warning',
  mastered: 'success',
}

const stateLabel: Record<CompetencyWithState['state'], string> = {
  locked: 'Locked',
  available: 'Available',
  learning: 'Learning',
  mastered: 'Mastered',
}

export function CompetencyCard({
  item,
  onActivity,
}: {
  item: CompetencyWithState
  onActivity: () => void
}) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { competency, mastery_score, state } = item
  const isLocked = state === 'locked'

  return (
    <Card className={clsx(isLocked && 'opacity-60')}>
      <button
        type="button"
        onClick={() => !isLocked && setIsExpanded((v) => !v)}
        disabled={isLocked}
        className="flex w-full items-center justify-between gap-3 text-left disabled:cursor-not-allowed"
      >
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-fg">{competency.name}</h3>
            <Badge tone={stateTone[state]}>{stateLabel[state]}</Badge>
          </div>
          <p className="mt-1 text-sm text-fg-muted">{competency.description}</p>
        </div>
        <div className="shrink-0 text-right">
          <span className="text-sm font-medium text-fg">{mastery_score.toFixed(0)}%</span>
        </div>
      </button>

      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-surface-raised">
        <div
          className="h-full rounded-full bg-accent"
          style={{ width: `${Math.min(100, mastery_score)}%` }}
        />
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-4 border-t border-border pt-4">
          <LogSessionForm
            competencyId={competency.id}
            onLogged={onActivity}
          />
          <ChallengeList competencyId={competency.id} onActivity={onActivity} />
        </div>
      )}
    </Card>
  )
}

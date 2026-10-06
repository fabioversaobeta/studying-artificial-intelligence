import { useAsync } from '@/hooks/use-async'
import { gamificationService } from '@/services/gamification-service'
import type { AchievementProgress, QuestProgress } from '@/types/api'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PageSpinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'

function AchievementCard({ item }: { item: AchievementProgress }) {
  const { achievement, earned, earned_at } = item
  return (
    <li>
      <Card className={earned ? 'border-success/40' : 'opacity-70'}>
        <div className="flex items-start gap-3">
          <span className="text-2xl" aria-hidden="true">
            {earned ? (achievement.icon ?? '🏆') : '🔒'}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-medium text-heading">{achievement.name}</h3>
              <Badge tone={earned ? 'success' : 'neutral'}>{earned ? 'Unlocked' : 'Locked'}</Badge>
            </div>
            <p className="mt-1 text-sm text-fg-muted">{achievement.description}</p>
            <p className="mt-2 text-xs text-fg-muted">
              +{achievement.xp_reward} XP
              {earned && earned_at && ` · earned ${new Date(earned_at).toLocaleDateString()}`}
            </p>
          </div>
        </div>
      </Card>
    </li>
  )
}

function QuestCard({ item }: { item: QuestProgress }) {
  const { quest, progress, target, completed } = item
  const pct = target > 0 ? Math.min(100, Math.round((progress / target) * 100)) : 0
  return (
    <li>
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-heading">{quest.title}</h3>
            <Badge tone="accent">{quest.period === 'weekly' ? 'Weekly' : 'One-time'}</Badge>
            {completed && <Badge tone="success">Completed</Badge>}
          </div>
          <span className="text-xs text-fg-muted">+{quest.xp_reward} XP</span>
        </div>
        <p className="mt-1 text-sm text-fg-muted">{quest.description}</p>
        <div className="mt-3 flex items-center gap-3">
          <div
            className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-raised"
            role="progressbar"
            aria-label={`${quest.title} progress`}
            aria-valuemin={0}
            aria-valuemax={target}
            aria-valuenow={Math.min(progress, target)}
          >
            <div
              className={completed ? 'h-full bg-success' : 'h-full bg-accent'}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs text-fg-muted">
            {Math.min(progress, target)} / {target}
          </span>
        </div>
      </Card>
    </li>
  )
}

export function AchievementsPage() {
  const achievements = useAsync(() => gamificationService.listAchievements(), [])
  const quests = useAsync(() => gamificationService.listQuests(), [])

  if (achievements.isLoading || quests.isLoading) return <PageSpinner />

  const earnedCount = achievements.data?.filter((a) => a.earned).length ?? 0

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-xl font-semibold text-heading">Achievements &amp; Quests</h1>
        <p className="mt-1 text-sm text-fg-muted">Milestones you have unlocked and goals in progress.</p>
      </div>

      <section aria-labelledby="quests-heading" className="space-y-3">
        <h2 id="quests-heading" className="font-medium text-heading">
          Quests
        </h2>
        {quests.error ? (
          <ErrorAlert message={quests.error} />
        ) : quests.data && quests.data.length > 0 ? (
          <ul className="space-y-3">
            {quests.data.map((q) => (
              <QuestCard key={q.quest.id} item={q} />
            ))}
          </ul>
        ) : (
          <p className="text-sm text-fg-muted">No quests available right now.</p>
        )}
      </section>

      <section aria-labelledby="achievements-heading" className="space-y-3">
        <h2 id="achievements-heading" className="font-medium text-heading">
          Achievements
          {achievements.data && (
            <span className="ml-2 text-sm font-normal text-fg-muted">
              {earnedCount} / {achievements.data.length} unlocked
            </span>
          )}
        </h2>
        {achievements.error ? (
          <ErrorAlert message={achievements.error} />
        ) : achievements.data && achievements.data.length > 0 ? (
          <ul className="grid gap-3 sm:grid-cols-2">
            {[...achievements.data]
              .sort((a, b) => Number(b.earned) - Number(a.earned))
              .map((a) => (
                <AchievementCard key={a.achievement.id} item={a} />
              ))}
          </ul>
        ) : (
          <p className="text-sm text-fg-muted">No achievements defined yet.</p>
        )}
      </section>
    </div>
  )
}

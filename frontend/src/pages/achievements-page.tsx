import { useAsync } from '@/hooks/use-async'
import { gamificationService } from '@/services/gamification-service'
import type { AchievementProgress, QuestProgress } from '@/types/api'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PageSpinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { useI18n, useT } from '@/i18n/use-i18n'

function AchievementCard({ item }: { item: AchievementProgress }) {
  const { achievement, earned, earned_at } = item
  const { t, formatDate, formatNumber } = useI18n()
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
              <Badge tone={earned ? 'success' : 'neutral'}>{earned ? t('achievements.unlocked') : t('achievements.locked')}</Badge>
            </div>
            <p className="mt-1 text-sm text-fg-muted">{achievement.description}</p>
            <p className="mt-2 text-xs text-fg-muted">
              {t('common.xpGain', { value: formatNumber(achievement.xp_reward) })}
              {earned && earned_at && ` · ${t('achievements.earnedOn', { date: formatDate(earned_at) })}`}
            </p>
          </div>
        </div>
      </Card>
    </li>
  )
}

function QuestCard({ item }: { item: QuestProgress }) {
  const { quest, progress, target, completed } = item
  const { t, formatNumber } = useI18n()
  const pct = target > 0 ? Math.min(100, Math.round((progress / target) * 100)) : 0
  return (
    <li>
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-heading">{quest.title}</h3>
            <Badge tone="accent">{quest.period === 'weekly' ? t('achievements.weekly') : t('achievements.oneTime')}</Badge>
            {completed && <Badge tone="success">{t('achievements.completed')}</Badge>}
          </div>
          <span className="text-xs text-fg-muted">
            {t('common.xpGain', { value: formatNumber(quest.xp_reward) })}
          </span>
        </div>
        <p className="mt-1 text-sm text-fg-muted">{quest.description}</p>
        <div className="mt-3 flex items-center gap-3">
          <div
            className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-raised"
            role="progressbar"
            aria-label={t('achievements.progressLabel', { title: quest.title })}
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
  const t = useT()

  if (achievements.isLoading || quests.isLoading) return <PageSpinner />

  const earnedCount = achievements.data?.filter((a) => a.earned).length ?? 0

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-xl font-semibold text-heading">{t('achievements.title')}</h1>
        <p className="mt-1 text-sm text-fg-muted">{t('achievements.subtitle')}</p>
      </div>

      <section aria-labelledby="quests-heading" className="space-y-3">
        <h2 id="quests-heading" className="font-medium text-heading">
          {t('achievements.quests')}
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
          <p className="text-sm text-fg-muted">{t('achievements.noQuests')}</p>
        )}
      </section>

      <section aria-labelledby="achievements-heading" className="space-y-3">
        <h2 id="achievements-heading" className="font-medium text-heading">
          {t('achievements.achievements')}
          {achievements.data && (
            <span className="ml-2 text-sm font-normal text-fg-muted">
              {t('achievements.unlockedCount', { earned: earnedCount, total: achievements.data.length })}
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
          <p className="text-sm text-fg-muted">{t('achievements.noAchievements')}</p>
        )}
      </section>
    </div>
  )
}

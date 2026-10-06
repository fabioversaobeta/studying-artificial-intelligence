import { Link } from 'react-router-dom'
import { useAsync } from '@/hooks/use-async'
import { learningService } from '@/services/learning-service'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PageSpinner } from '@/components/ui/spinner'
import { ErrorAlert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <Card>
      <p className="text-xs font-medium uppercase tracking-wide text-fg-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-heading">{value}</p>
      {hint && <p className="mt-1 text-xs text-fg-muted">{hint}</p>}
    </Card>
  )
}

export function DashboardPage() {
  const { data, error, isLoading } = useAsync(() => learningService.getDashboard(), [])

  if (isLoading) return <PageSpinner />
  if (error) return <ErrorAlert message={error} />
  if (!data) return null

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-heading">Dashboard</h1>
        <p className="mt-1 text-sm text-fg-muted">Where you stand today.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Level" value={data.level} hint={`${data.xp_to_next_level} XP to next`} />
        <StatCard label="Total XP" value={data.total_xp} />
        <StatCard label="Streak" value={`${data.current_streak_days}d`} hint={`Best: ${data.longest_streak_days}d`} />
        <Link to="/reviews" aria-label={`Due reviews: ${data.due_review_count}. Open reviews`}>
          <StatCard
            label="Due Reviews"
            value={data.due_review_count}
            hint={data.due_review_count > 0 ? 'Review now →' : undefined}
          />
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-medium text-heading">Active Goals</h2>
            <Link to="/goals" className="text-sm text-accent-light hover:underline">
              Manage
            </Link>
          </div>
          {data.active_goals.length === 0 ? (
            <p className="text-sm text-fg-muted">
              No active goals yet.{' '}
              <Link to="/goals" className="text-accent-light hover:underline">
                Set one
              </Link>
              .
            </p>
          ) : (
            <ul className="space-y-2">
              {data.active_goals.map((goal) => (
                <li key={goal.id} className="text-sm text-fg">
                  {goal.title}
                  {goal.target_date && (
                    <span className="ml-2 text-xs text-fg-muted">by {goal.target_date}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <h2 className="mb-3 font-medium text-heading">Weakest Competencies</h2>
          {data.weakest_competencies.length === 0 ? (
            <p className="text-sm text-fg-muted">
              Nothing tracked yet.{' '}
              <Link to="/subjects" className="text-accent-light hover:underline">
                Start studying
              </Link>
              .
            </p>
          ) : (
            <ul className="space-y-2">
              {data.weakest_competencies.map((m) => (
                <li key={m.competency_id} className="flex items-center justify-between text-sm">
                  <span className="text-fg-muted">Competency {m.competency_id.slice(0, 8)}</span>
                  <Badge tone={m.score < 40 ? 'danger' : m.score < 80 ? 'warning' : 'success'}>
                    {m.score.toFixed(0)}%
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card>
        <h2 className="mb-3 font-medium text-heading">Recent Study Sessions</h2>
        {data.recent_study_sessions.length === 0 ? (
          <div className="flex items-center justify-between">
            <p className="text-sm text-fg-muted">No study sessions logged yet.</p>
            <Link to="/subjects">
              <Button variant="secondary">Browse Subjects</Button>
            </Link>
          </div>
        ) : (
          <ul className="space-y-2">
            {data.recent_study_sessions.map((s) => (
              <li key={s.id} className="flex items-center justify-between text-sm">
                <span className="text-fg">{s.notes ?? 'Study session'}</span>
                <span className="text-fg-muted">
                  {s.duration_minutes} min · {new Date(s.occurred_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}

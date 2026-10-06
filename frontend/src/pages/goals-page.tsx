import { useState, type FormEvent } from 'react'
import { useAsync } from '@/hooks/use-async'
import { learningService } from '@/services/learning-service'
import { ApiError } from '@/services/api-client'
import { useToast } from '@/features/feedback/toast-context'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input, Label, Textarea } from '@/components/ui/input'
import { ErrorAlert } from '@/components/ui/alert'
import { PageSpinner } from '@/components/ui/spinner'
import type { GoalStatus } from '@/types/api'

const statusTone: Record<GoalStatus, 'accent' | 'success' | 'neutral'> = {
  active: 'accent',
  achieved: 'success',
  archived: 'neutral',
}

export function GoalsPage() {
  const { data: goals, error, isLoading, refetch } = useAsync(() => learningService.listGoals(), [])
  const toast = useToast()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    setIsSubmitting(true)
    try {
      await learningService.createGoal({
        title,
        description: description.trim() || undefined,
      })
      setTitle('')
      setDescription('')
      refetch()
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Could not create goal')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function updateStatus(goalId: string, status: GoalStatus) {
    try {
      await learningService.updateGoalStatus(goalId, status)
      refetch()
    } catch (err) {
      toast.showError(err, 'Could not update goal')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-heading">Learning Goals</h1>
        <p className="mt-1 text-sm text-fg-muted">What are you working toward?</p>
      </div>

      <Card>
        <form onSubmit={handleCreate} className="space-y-3">
          {formError && <ErrorAlert message={formError} />}
          <div>
            <Label htmlFor="goal-title">Title</Label>
            <Input
              id="goal-title"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Become interview-ready for senior backend roles"
            />
          </div>
          <div>
            <Label htmlFor="goal-description">Description (optional)</Label>
            <Textarea
              id="goal-description"
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Adding…' : 'Add goal'}
          </Button>
        </form>
      </Card>

      {isLoading ? (
        <PageSpinner />
      ) : error ? (
        <ErrorAlert message={error} />
      ) : (
        <div className="space-y-3">
          {goals?.map((goal) => (
            <Card key={goal.id}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-fg">{goal.title}</h3>
                    <Badge tone={statusTone[goal.status]}>{goal.status}</Badge>
                  </div>
                  {goal.description && (
                    <p className="mt-1 text-sm text-fg-muted">{goal.description}</p>
                  )}
                </div>
                {goal.status === 'active' && (
                  <div className="flex shrink-0 gap-2">
                    <Button variant="secondary" onClick={() => updateStatus(goal.id, 'achieved')}>
                      Mark achieved
                    </Button>
                    <Button variant="ghost" onClick={() => updateStatus(goal.id, 'archived')}>
                      Archive
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
          {goals?.length === 0 && (
            <p className="text-sm text-fg-muted">No goals yet — add your first one above.</p>
          )}
        </div>
      )}
    </div>
  )
}

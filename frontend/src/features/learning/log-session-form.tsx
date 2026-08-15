import { useState, type FormEvent } from 'react'
import { learningService } from '@/services/learning-service'
import { ApiError } from '@/services/api-client'
import { Button } from '@/components/ui/button'
import { Input, Label, Textarea } from '@/components/ui/input'
import { ErrorAlert } from '@/components/ui/alert'

export function LogSessionForm({
  competencyId,
  onLogged,
}: {
  competencyId: string
  onLogged: () => void
}) {
  const [duration, setDuration] = useState(30)
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await learningService.logStudySession({
        competency_id: competencyId,
        duration_minutes: duration,
        notes: notes.trim() || undefined,
      })
      setNotes('')
      onLogged()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not log session')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && <ErrorAlert message={error} />}
      <div className="flex items-end gap-3">
        <div className="w-28">
          <Label htmlFor={`duration-${competencyId}`}>Minutes</Label>
          <Input
            id={`duration-${competencyId}`}
            type="number"
            min={1}
            max={600}
            required
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
          />
        </div>
        <div className="flex-1">
          <Label htmlFor={`notes-${competencyId}`}>Notes (optional)</Label>
          <Textarea
            id={`notes-${competencyId}`}
            rows={1}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="What did you study?"
          />
        </div>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Logging…' : 'Log session'}
        </Button>
      </div>
    </form>
  )
}

import { useEffect, useState, type FormEvent } from 'react'
import { authService } from '@/services/auth-service'
import { userService } from '@/services/user-service'
import { useAsync } from '@/hooks/use-async'
import { useToast } from '@/features/feedback/toast-context'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input, Label } from '@/components/ui/input'
import { ErrorAlert } from '@/components/ui/alert'
import { PageSpinner } from '@/components/ui/spinner'
import type { Language } from '@/types/api'

const LANGUAGE_OPTIONS: { value: Language; label: string }[] = [
  { value: 'en', label: 'English' },
  { value: 'pt-BR', label: 'Português (Brasil)' },
]

export function SettingsPage() {
  const { data: user, error, isLoading, refetch } = useAsync(() => authService.me(), [])
  const toast = useToast()
  const [displayName, setDisplayName] = useState('')
  const [language, setLanguage] = useState<Language>('en')
  const [isSaving, setIsSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name)
      setLanguage(user.preferred_language)
    }
  }, [user])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    setIsSaving(true)
    try {
      const updated = await userService.updateMe({
        display_name: displayName.trim(),
        preferred_language: language,
      })
      setDisplayName(updated.display_name)
      setLanguage(updated.preferred_language)
      toast.show('Settings saved', 'success')
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Could not save settings')
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) return <PageSpinner />
  if (error) return <ErrorAlert message={error} onRetry={refetch} />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-heading">Settings</h1>
        <p className="mt-1 text-sm text-fg-muted">Your profile and content preferences.</p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          {formError && <ErrorAlert message={formError} />}
          <div>
            <Label htmlFor="settings-display-name">Display name</Label>
            <Input
              id="settings-display-name"
              required
              maxLength={100}
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="settings-language">Content language</Label>
            <select
              id="settings-language"
              value={language}
              onChange={(e) => setLanguage(e.target.value as Language)}
              aria-describedby="settings-language-hint"
              className="w-full rounded-xl border border-border-strong bg-surface-raised px-3.5 py-2.5 text-sm text-fg focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent"
            >
              {LANGUAGE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p id="settings-language-hint" className="mt-1.5 text-xs text-fg-muted">
              Applies to quiz questions and explanations. Content without a translation falls back
              to English. The interface itself stays in English for now.
            </p>
          </div>
          <Button type="submit" disabled={isSaving || displayName.trim() === ''}>
            {isSaving ? 'Saving…' : 'Save changes'}
          </Button>
        </form>
      </Card>
    </div>
  )
}

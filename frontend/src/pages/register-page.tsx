import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/use-auth'
import { ApiError } from '@/services/api-client'
import { authService } from '@/services/auth-service'
import type { RegistrationInfo } from '@/types/api'
import { Button } from '@/components/ui/button'
import { Input, Label } from '@/components/ui/input'
import { ErrorAlert } from '@/components/ui/alert'
import { useT } from '@/i18n/use-i18n'

export function RegisterPage() {
  const { register } = useAuth()
  const t = useT()
  const navigate = useNavigate()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  const [info, setInfo] = useState<RegistrationInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Best effort: if this fails the form still works (the backend enforces the policy).
  useEffect(() => {
    authService
      .registrationInfo()
      .then(setInfo)
      .catch(() => undefined)
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await register(email, password, displayName, inviteCode.trim() || undefined)
      navigate('/')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('register.error'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-semibold text-heading">{t('register.title')}</h2>
      {error && <ErrorAlert message={error} />}
      {info && !info.enabled && <ErrorAlert message={t('register.closed')} />}
      <div>
        <Label htmlFor="displayName">{t('register.name')}</Label>
        <Input
          id="displayName"
          required
          autoComplete="name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
        />
      </div>
      <div>
        <Label htmlFor="email">{t('register.email')}</Label>
        <Input
          id="email"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <div>
        <Label htmlFor="password">{t('register.password')}</Label>
        <Input
          id="password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <p className="mt-1 text-xs text-fg-muted">{t('register.passwordHint')}</p>
      </div>
      {info?.invite_required && (
        <div>
          <Label htmlFor="inviteCode">{t('register.inviteCode')}</Label>
          <Input
            id="inviteCode"
            required
            autoComplete="off"
            value={inviteCode}
            onChange={(e) => setInviteCode(e.target.value)}
          />
        </div>
      )}
      <Button type="submit" className="w-full" disabled={isSubmitting || info?.enabled === false}>
        {isSubmitting ? t('register.submitting') : t('register.submit')}
      </Button>
      <p className="text-center text-sm text-fg-muted">
        {t('register.haveAccount')}{' '}
        <Link to="/login" className="text-accent-light hover:underline">
          {t('register.loginLink')}
        </Link>
      </p>
    </form>
  )
}

import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/use-auth'
import { ApiError } from '@/services/api-client'
import { Button } from '@/components/ui/button'
import { Input, Label } from '@/components/ui/input'
import { ErrorAlert } from '@/components/ui/alert'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await register(email, password, displayName)
      navigate('/')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to register')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-semibold text-heading">Create your account</h2>
      {error && <ErrorAlert message={error} />}
      <div>
        <Label htmlFor="displayName">Name</Label>
        <Input
          id="displayName"
          required
          autoComplete="name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
        />
      </div>
      <div>
        <Label htmlFor="email">Email</Label>
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
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <p className="mt-1 text-xs text-fg-muted">At least 8 characters.</p>
      </div>
      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? 'Creating account…' : 'Create account'}
      </Button>
      <p className="text-center text-sm text-fg-muted">
        Already have an account?{' '}
        <Link to="/login" className="text-accent-light hover:underline">
          Log in
        </Link>
      </p>
    </form>
  )
}

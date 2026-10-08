import type { ReactNode } from 'react'
import { useT } from '@/i18n/use-i18n'

export function AuthLayout({ children }: { children: ReactNode }) {
  const t = useT()
  return (
    <main className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold text-heading">{t('common.appName')}</h1>
          <p className="mt-1 text-sm text-fg-muted">{t('auth.tagline')}</p>
        </div>
        <div className="rounded-2xl border border-border bg-surface p-6">{children}</div>
      </div>
    </main>
  )
}

import type { ReactNode } from 'react'

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold text-heading">Learning Platform</h1>
          <p className="mt-1 text-sm text-fg-muted">Track your growth, one competency at a time.</p>
        </div>
        <div className="rounded-2xl border border-border bg-surface p-6">{children}</div>
      </div>
    </main>
  )
}

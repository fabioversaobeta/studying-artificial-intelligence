import { NavLink, Outlet } from 'react-router-dom'
import clsx from 'clsx'
import { useAuth } from '@/hooks/use-auth'
import { useAsync } from '@/hooks/use-async'
import { gamificationService } from '@/services/gamification-service'
import { Button } from '@/components/ui/button'
import { useT } from '@/i18n/use-i18n'
import type { MessageKey } from '@/i18n'

const navItems: { to: string; label: MessageKey; end?: boolean }[] = [
  { to: '/', label: 'nav.dashboard', end: true },
  { to: '/subjects', label: 'nav.subjects' },
  { to: '/learning-paths', label: 'nav.paths' },
  { to: '/goals', label: 'nav.goals' },
  { to: '/quizzes', label: 'nav.quizzes' },
  { to: '/reviews', label: 'nav.reviews' },
  { to: '/achievements', label: 'nav.achievements' },
  { to: '/settings', label: 'nav.settings' },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const t = useT()
  const { data: profile } = useAsync(() => gamificationService.getProfile(), [])

  return (
    <div className="min-h-screen bg-bg">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-accent focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-bg"
      >
        {t('nav.skip')}
      </a>
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-8">
            <span className="text-sm font-semibold text-heading">{t('common.appName')}</span>
            <nav aria-label={t('nav.main')} className="flex items-center gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    clsx(
                      'rounded-full px-3 py-1.5 text-sm font-medium transition-colors',
                      isActive ? 'bg-accent/15 text-accent-light' : 'text-fg-muted hover:text-fg',
                    )
                  }
                >
                  {t(item.label)}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {profile && (
              <div className="flex items-center gap-3 text-sm">
                <span className="rounded-full bg-accent/15 px-2.5 py-0.5 font-medium text-accent-light">
                  {t('nav.level', { level: profile.level })}
                </span>
                <span className="text-fg-muted">{t('common.xp', { value: profile.total_xp })}</span>
                {profile.current_streak_days > 0 && (
                  <span
                    className="text-fg-muted"
                    aria-label={t('nav.streakLabel', { count: profile.current_streak_days })}
                  >
                    <span aria-hidden="true">🔥 {t('nav.streakShort', { count: profile.current_streak_days })}</span>
                  </span>
                )}
              </div>
            )}
            <span className="text-sm text-fg-muted">{user?.display_name}</span>
            <Button variant="ghost" onClick={logout}>
              {t('nav.logout')}
            </Button>
          </div>
        </div>
      </header>

      <main id="main-content" tabIndex={-1} className="mx-auto max-w-5xl px-4 py-8 focus:outline-none">
        <Outlet />
      </main>
    </div>
  )
}

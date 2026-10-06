import { NavLink, Outlet } from 'react-router-dom'
import clsx from 'clsx'
import { useAuth } from '@/hooks/use-auth'
import { useAsync } from '@/hooks/use-async'
import { gamificationService } from '@/services/gamification-service'
import { Button } from '@/components/ui/button'

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/subjects', label: 'Subjects' },
  { to: '/learning-paths', label: 'Paths' },
  { to: '/goals', label: 'Goals' },
  { to: '/reviews', label: 'Reviews' },
  { to: '/achievements', label: 'Achievements' },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const { data: profile } = useAsync(() => gamificationService.getProfile(), [])

  return (
    <div className="min-h-screen bg-bg">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-accent focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-bg"
      >
        Skip to main content
      </a>
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-8">
            <span className="text-sm font-semibold text-heading">Learning Platform</span>
            <nav aria-label="Main" className="flex items-center gap-1">
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
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {profile && (
              <div className="flex items-center gap-3 text-sm">
                <span className="rounded-full bg-accent/15 px-2.5 py-0.5 font-medium text-accent-light">
                  Lv {profile.level}
                </span>
                <span className="text-fg-muted">{profile.total_xp} XP</span>
                {profile.current_streak_days > 0 && (
                  <span
                    className="text-fg-muted"
                    aria-label={`${profile.current_streak_days} day streak`}
                  >
                    <span aria-hidden="true">🔥 {profile.current_streak_days}d</span>
                  </span>
                )}
              </div>
            )}
            <span className="text-sm text-fg-muted">{user?.display_name}</span>
            <Button variant="ghost" onClick={logout}>
              Log out
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

import { NavLink, Outlet } from 'react-router-dom'
import clsx from 'clsx'
import { useAuth } from '@/hooks/use-auth'
import { useAsync } from '@/hooks/use-async'
import { gamificationService } from '@/services/gamification-service'
import { Button } from '@/components/ui/button'

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/subjects', label: 'Subjects' },
  { to: '/goals', label: 'Goals' },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const { data: profile } = useAsync(() => gamificationService.getProfile(), [])

  return (
    <div className="min-h-screen bg-bg">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-8">
            <span className="text-sm font-semibold text-heading">Learning Platform</span>
            <nav className="flex items-center gap-1">
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
                  <span className="text-fg-muted">🔥 {profile.current_streak_days}d</span>
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

      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}

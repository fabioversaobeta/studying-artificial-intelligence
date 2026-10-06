import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AppLayout } from '@/layouts/app-layout'

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => ({ user: { display_name: 'Ada' }, logout: vi.fn() }),
}))
vi.mock('@/services/gamification-service', () => ({
  gamificationService: { getProfile: vi.fn(() => new Promise(() => undefined)) },
}))

describe('AppLayout accessibility landmarks', () => {
  it('exposes a skip link, a labelled nav and a focusable main landmark', () => {
    render(
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'Skip to main content' })).toHaveAttribute(
      'href',
      '#main-content',
    )
    expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument()
    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('main')).toHaveAttribute('id', 'main-content')
  })
})

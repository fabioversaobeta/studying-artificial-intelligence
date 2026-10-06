import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ToastProvider, useToast } from '@/features/feedback/toast-context'
import { ApiError } from '@/services/api-client'

function Trigger({ err }: { err: unknown }) {
  const toast = useToast()
  return <button onClick={() => toast.showError(err, 'Fallback msg')}>go</button>
}

afterEach(() => vi.useRealTimers())

describe('ToastProvider', () => {
  it('shows the ApiError message in an alert and dismisses on click', async () => {
    render(
      <ToastProvider>
        <Trigger err={new ApiError('x', 'Server said no', 500)} />
      </ToastProvider>,
    )
    await userEvent.click(screen.getByText('go'))
    expect(screen.getByRole('alert')).toHaveTextContent('Server said no')
    await userEvent.click(screen.getByRole('button', { name: 'Dismiss notification' }))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('uses the fallback for unknown errors and auto-dismisses', () => {
    vi.useFakeTimers()
    render(
      <ToastProvider>
        <Trigger err={new Error('raw')} />
      </ToastProvider>,
    )
    act(() => screen.getByText('go').click())
    expect(screen.getByRole('alert')).toHaveTextContent('Fallback msg')
    act(() => {
      vi.advanceTimersByTime(7000)
    })
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

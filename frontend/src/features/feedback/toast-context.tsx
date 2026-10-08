import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { ApiError } from '@/services/api-client'
import { useT } from '@/i18n/use-i18n'

type ToastTone = 'error' | 'success' | 'info'

interface Toast {
  id: number
  tone: ToastTone
  message: string
}

interface ToastApi {
  show: (message: string, tone?: ToastTone) => void
  /** Shows an error toast using the ApiError message when available. */
  showError: (err: unknown, fallback?: string) => void
}

const ToastContext = createContext<ToastApi | null>(null)

const AUTO_DISMISS_MS = 6000

const toneClasses: Record<ToastTone, string> = {
  error: 'border-danger/40 text-danger',
  success: 'border-success/40 text-success',
  info: 'border-border text-fg',
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const nextId = useRef(1)
  const t = useT()

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const show = useCallback(
    (message: string, tone: ToastTone = 'info') => {
      const id = nextId.current++
      setToasts((prev) => [...prev, { id, tone, message }])
      setTimeout(() => dismiss(id), AUTO_DISMISS_MS)
    },
    [dismiss],
  )

  const showError = useCallback(
    (err: unknown, fallback = t('common.somethingWrong')) =>
      show(err instanceof ApiError ? err.message : fallback, 'error'),
    [show, t],
  )

  const api = useMemo(() => ({ show, showError }), [show, showError])

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2">
        {toasts.map((item) => (
          <div
            key={item.id}
            role={item.tone === 'error' ? 'alert' : 'status'}
            className={`flex items-start justify-between gap-3 rounded-xl border bg-surface-raised px-4 py-3 text-sm shadow-lg ${toneClasses[item.tone]}`}
          >
            <span>{item.message}</span>
            <button
              type="button"
              aria-label={t('common.dismissNotification')}
              onClick={() => dismiss(item.id)}
              className="text-fg-muted hover:text-fg"
            >
              <span aria-hidden="true">×</span>
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast(): ToastApi {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}

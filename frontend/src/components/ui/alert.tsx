import { Button } from '@/components/ui/button'
import { useT } from '@/i18n/use-i18n'

/** Error message announced to assistive tech (role="alert"); optional retry action. */
export function ErrorAlert({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const t = useT()
  return (
    <div
      role="alert"
      className="flex items-center justify-between gap-3 rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
    >
      <span>{message}</span>
      {onRetry && (
        <Button type="button" variant="danger" onClick={onRetry}>
          {t('common.retry')}
        </Button>
      )}
    </div>
  )
}

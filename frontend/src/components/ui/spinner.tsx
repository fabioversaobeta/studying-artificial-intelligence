import clsx from 'clsx'
import { useT } from '@/i18n/use-i18n'

export function Spinner({ className }: { className?: string }) {
  const t = useT()
  return (
    <div
      className={clsx(
        'h-5 w-5 animate-spin rounded-full border-2 border-fg-muted border-t-accent',
        className,
      )}
      role="status"
      aria-label={t('common.loading')}
    />
  )
}

export function PageSpinner() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <Spinner className="h-8 w-8" />
    </div>
  )
}

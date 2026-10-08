import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { I18nContext } from '@/i18n/context'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/** Catches render-time errors anywhere below it so the app never white-screens. */
export class ErrorBoundary extends Component<Props, State> {
  static contextType = I18nContext
  declare context: React.ContextType<typeof I18nContext>
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled UI error', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    const { t } = this.context
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg px-4">
        <div
          role="alert"
          className="w-full max-w-md rounded-2xl border border-danger/30 bg-surface p-6"
        >
          <h1 className="text-lg font-semibold text-heading">{t('errorBoundary.title')}</h1>
          <p className="mt-2 text-sm text-fg-muted">
            {t('errorBoundary.body')}
          </p>
          <div className="mt-4 flex gap-2">
            <Button onClick={() => window.location.reload()}>{t('errorBoundary.reload')}</Button>
            <Button variant="secondary" onClick={() => this.setState({ error: null })}>
              {t('errorBoundary.tryAgain')}
            </Button>
          </div>
        </div>
      </div>
    )
  }
}

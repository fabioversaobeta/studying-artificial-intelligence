import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/** Catches render-time errors anywhere below it so the app never white-screens. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled UI error', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg px-4">
        <div
          role="alert"
          className="w-full max-w-md rounded-2xl border border-danger/30 bg-surface p-6"
        >
          <h1 className="text-lg font-semibold text-heading">Something went wrong</h1>
          <p className="mt-2 text-sm text-fg-muted">
            An unexpected error occurred. Reloading the page usually fixes it.
          </p>
          <div className="mt-4 flex gap-2">
            <Button onClick={() => window.location.reload()}>Reload page</Button>
            <Button variant="secondary" onClick={() => this.setState({ error: null })}>
              Try again
            </Button>
          </div>
        </div>
      </div>
    )
  }
}

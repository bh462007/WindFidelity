import type { ErrorKind } from '../api/client'

export function Loading() {
  return (
    <div className="state" role="status">
      Loading…
    </div>
  )
}

interface ErrorStateProps {
  kind: ErrorKind
  message: string
  onRetry: () => void
}

export function ErrorState({ kind, message, onRetry }: ErrorStateProps) {
  if (kind === 'no_data') {
    return (
      <div className="state">
        <h2>No data for this day</h2>
        <p>Forecasts and actuals haven't been published for this day. Pick another day.</p>
      </div>
    )
  }

  if (kind === 'invalid') {
    return (
      <div className="state">
        <h2>That date isn't valid</h2>
        <p>{message}</p>
      </div>
    )
  }

  return (
    <div className="state" role="alert">
      <h2>Data unavailable</h2>
      <p>The data couldn't be loaded. If this keeps happening, check that the backend is running.</p>
      {message && <p className="detail">{message}</p>}
      <button type="button" onClick={onRetry}>
        Retry
      </button>
    </div>
  )
}
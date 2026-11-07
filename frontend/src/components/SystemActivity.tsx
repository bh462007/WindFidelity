import type { ActivityEvent, ActivityKind } from '../api/client'
import { ACTIVITY_REFRESH_MS } from '../hooks/useActivity'
import type { ActivityState } from '../hooks/useActivity'

const KIND_LABEL: Record<ActivityKind, string> = {
  ingestion: 'Ingestion',
  match: 'Match',
  cache: 'Cache',
  error: 'Error',
}

const timeOf = (timestamp: string) => timestamp.slice(11, 19)

function isPartialMatch(event: ActivityEvent) {
  return (
    event.kind === 'match' &&
    Number(event.details.matched_hours) < Number(event.details.expected_hours)
  )
}

function eventClass(event: ActivityEvent) {
  return event.kind === 'error' || isPartialMatch(event) ? 'event event-warn' : 'event'
}

export function SystemActivity({ state }: { state: ActivityState }) {
  return (
    <section className="panel activity" aria-labelledby="activity-title">
      <h2 id="activity-title">System Activity</h2>

      {state.status === 'loading' && <p>Loading activity…</p>}

      {state.status === 'error' && (
        <p className="warn" role="alert">
          Activity feed unavailable. The backend isn't responding.
        </p>
      )}

      {state.status === 'ready' && (
        <>
          <dl>
            <dt>Cache</dt>
            <dd className={state.ready.status === 'ready' ? 'pos' : 'warn'}>
              {state.ready.status}
            </dd>
            <dt>Days cached</dt>
            <dd>{state.ready.cached_days}</dd>
          </dl>

          {state.activity.events.length === 0 ? (
            <p>No pipeline events yet. Events appear when a day is analysed.</p>
          ) : (
            <ol className="events">
              {state.activity.events.map((event) => (
                <li key={event.id} className={eventClass(event)}>
                  <time dateTime={event.timestamp}>{timeOf(event.timestamp)}</time>
                  <span className="kind">{KIND_LABEL[event.kind]}</span>
                  <span className="msg">{event.message}</span>
                </li>
              ))}
            </ol>
          )}

          <p className="caption">
            Times are UTC. Refreshes every {ACTIVITY_REFRESH_MS / 1000} seconds.
          </p>
        </>
      )}
    </section>
  )
}
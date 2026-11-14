import { useState } from 'react'
import './App.css'
import { DayView } from './components/DayView'
import { MonthOverview } from './components/MonthOverview'
import { ErrorState, Loading } from './components/States'
import { SystemActivity } from './components/SystemActivity'
import { useActivity } from './hooks/useActivity'
import { useSnapshot } from './hooks/useSnapshot'

type View = 'month' | 'day'

const PREFERRED_DAY = '2026-01-15'

export default function App() {
  const [view, setView] = useState<View>('month')
  const [day, setDay] = useState<string | null>(null)
  const { state, retry } = useSnapshot()
  const activity = useActivity(`${view}:${state.status}`)

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <h1>WindFidelity</h1>
          <p>Day-ahead wind forecast accuracy, Great Britain</p>
        </div>
        <div className="view-switch" role="group" aria-label="View">
          <button type="button" aria-pressed={view === 'month'} onClick={() => setView('month')}>
            January overview
          </button>
          <button type="button" aria-pressed={view === 'day'} onClick={() => setView('day')}>
            Single day
          </button>
        </div>
      </header>

      <div className="layout">
        <main className="main">
          {state.status === 'loading' && <Loading />}
          {state.status === 'error' && (
            <ErrorState kind={state.kind} message={state.message} onRetry={retry} />
          )}
          {state.status === 'ready' && view === 'month' && <MonthOverview snapshot={state.snapshot} />}
          {state.status === 'ready' && view === 'day' && (
            <DayView
              snapshot={state.snapshot}
              day={day ?? defaultDay(state.snapshot.period)}
              onDayChange={setDay}
            />
          )}
        </main>

        <aside className="rail">
          {state.status === 'ready' && (
            <section className="panel">
              <SystemActivity state={activity} />
              <h2>How this is scored</h2>
              <p>{state.snapshot.forecast_cutoff.policy}</p>
            </section>
          )}
        </aside>
      </div>
    </div>
  )
}

function defaultDay(period: { start: string; end: string }) {
  return PREFERRED_DAY >= period.start && PREFERRED_DAY <= period.end ? PREFERRED_DAY : period.start
}
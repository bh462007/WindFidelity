import { useState } from 'react'
import './App.css'
import { ErrorState, Loading } from './components/States'
import { useAnalysis } from './hooks/useAnalysis'
import { SummaryCards } from './components/SummaryCards'
import { GenerationChart } from './components/GenerationChart'
import { ErrorChart } from './components/ErrorChart'
import { SystemActivity } from './components/SystemActivity'
import { useActivity } from './hooks/useActivity'

  
const DEFAULT_DAY = '2026-01-15'

export default function App() {
  const [day, setDay] = useState(DEFAULT_DAY)
  const { state, retry } = useAnalysis(day)
  const activity = useActivity(`${day}:${state.status}`)

    return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <h1>WindFidelity</h1>
          <p>Day-ahead wind forecast accuracy, Great Britain</p>
        </div>
        <label className="day-picker">
          Delivery day
          <input
            type="date"
            value={day}
            onChange={(e) => e.target.value && setDay(e.target.value)}
          />
        </label>
      </header>

      <div className="layout">
        <main className="main">
          {state.status === 'loading' && <Loading />}
          {state.status === 'error' && (
            <ErrorState kind={state.kind} message={state.message} onRetry={retry} />
          )}
          {state.status === 'ready' &&
            (state.series.points.length === 0 ? (
              <ErrorState kind="no_data" message="" onRetry={retry} />
            ) : (
              <>
                <SummaryCards summary={state.summary} />
                <GenerationChart points={state.series.points} />
                <ErrorChart points={state.series.points} />
              </>
            ))}
        </main>

        <aside className="rail">
          {state.status === 'ready' && (
            <section className="panel">
              <SystemActivity state={activity} />
              <h2>How this is scored</h2>
              <p>{state.summary.forecast_cutoff.policy}</p>
            </section>
          )}
        </aside>
      </div>
    </div>
  )
}
import { useState } from 'react'
import './App.css'
import { ErrorState, Loading } from './components/States'
import { useAnalysis } from './hooks/useAnalysis'
import { SummaryCards } from './components/SummaryCards'
import { GenerationChart } from './components/GenerationChart'
import { ErrorChart } from './components/ErrorChart'

const DEFAULT_DAY = '2026-01-15'

export default function App() {
  const [day, setDay] = useState(DEFAULT_DAY)
  const { state, retry } = useAnalysis(day)

  return (
    <main className="app">
      <header>
        <h1>WindFidelity</h1>
        <p>Day-ahead wind forecast accuracy, Great Britain</p>
        <label>
          Delivery day{' '}
          <input
            type="date"
            value={day}
            onChange={(e) => e.target.value && setDay(e.target.value)}
          />
        </label>
      </header>

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
  )
}
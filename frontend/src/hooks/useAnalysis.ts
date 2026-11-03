import { useCallback, useEffect, useState } from 'react'
import { ApiError, fetchSummary, fetchTimeseries } from '../api/client'
import type { ErrorKind, Summary, Timeseries } from '../api/client'

export type AnalysisState =
  | { status: 'loading' }
  | { status: 'error'; kind: ErrorKind; message: string }
  | { status: 'ready'; summary: Summary; series: Timeseries }

type Outcome = Exclude<AnalysisState, { status: 'loading' }>

export function useAnalysis(day: string) {
  const [attempt, setAttempt] = useState(0)
  const [result, setResult] = useState<{ key: string; outcome: Outcome } | null>(null)
  const key = `${day}#${attempt}`

  useEffect(() => {
    const controller = new AbortController()

    async function load() {
      try {
        const summary = await fetchSummary(day, controller.signal)
        const series = await fetchTimeseries(day, controller.signal)
        setResult({ key, outcome: { status: 'ready', summary, series } })
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return
        const apiError =
          err instanceof ApiError ? err : new ApiError('unknown', 'Unexpected error')
        setResult({
          key,
          outcome: { status: 'error', kind: apiError.kind, message: apiError.message },
        })
      }
    }

    void load()
    return () => controller.abort()
  }, [day, key])

  const state: AnalysisState =
    result && result.key === key ? result.outcome : { status: 'loading' }
  const retry = useCallback(() => setAttempt((a) => a + 1), [])

  return { state, retry }
}
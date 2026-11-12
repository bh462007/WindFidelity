import { useCallback, useEffect, useState } from 'react'
import { ApiError, fetchSnapshot } from '../api/client'
import type { ErrorKind, Snapshot } from '../api/client'

export type SnapshotState =
  | { status: 'loading' }
  | { status: 'error'; kind: ErrorKind; message: string }
  | { status: 'ready'; snapshot: Snapshot }

type Outcome = Exclude<SnapshotState, { status: 'loading' }>

export function useSnapshot() {
  const [attempt, setAttempt] = useState(0)
  const [result, setResult] = useState<{ attempt: number; outcome: Outcome } | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function load() {
      try {
        const snapshot = await fetchSnapshot(controller.signal)
        setResult({ attempt, outcome: { status: 'ready', snapshot } })
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return
        const apiError =
          err instanceof ApiError ? err : new ApiError('unknown', 'Unexpected error')
        setResult({
          attempt,
          outcome: { status: 'error', kind: apiError.kind, message: apiError.message },
        })
      }
    }

    void load()
    return () => controller.abort()
  }, [attempt])

  const state: SnapshotState =
    result && result.attempt === attempt ? result.outcome : { status: 'loading' }
  const retry = useCallback(() => setAttempt((a) => a + 1), [])

  return { state, retry }
}
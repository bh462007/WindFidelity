import { useEffect, useState } from 'react'
import { fetchActivity, fetchReady } from '../api/client'
import type { Activity, Ready } from '../api/client'

export const ACTIVITY_REFRESH_MS = 10_000
const EVENT_LIMIT = 30

export type ActivityState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'ready'; ready: Ready; activity: Activity }

export function useActivity(refreshKey: string): ActivityState {
  const [state, setState] = useState<ActivityState>({ status: 'loading' })

  useEffect(() => {
    const controller = new AbortController()

    async function load() {
      try {
        const [ready, activity] = await Promise.all([
          fetchReady(controller.signal),
          fetchActivity(EVENT_LIMIT, controller.signal),
        ])
        setState({ status: 'ready', ready, activity })
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return
        setState({ status: 'error' })
      }
    }

    void load()
    const timer = window.setInterval(() => {
      if (!document.hidden) void load()
    }, ACTIVITY_REFRESH_MS)

    return () => {
      controller.abort()
      window.clearInterval(timer)
    }
  }, [refreshKey])

  return state
}
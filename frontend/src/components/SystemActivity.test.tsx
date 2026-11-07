import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { ActivityEvent } from '../api/client'
import type { ActivityState } from '../hooks/useActivity'
import { SystemActivity } from './SystemActivity'

const event = (overrides: Partial<ActivityEvent> = {}): ActivityEvent => ({
  id: 1,
  timestamp: '2026-11-06T16:33:08Z',
  kind: 'ingestion',
  message: 'FUELHH 2026-01-15: 48 wind rows loaded',
  details: { rows: 48 },
  ...overrides,
})

const ready = (
  events: ActivityEvent[],
  status: 'ready' | 'warming' = 'ready',
  cachedDays = 1,
): ActivityState => ({
  status: 'ready',
  ready: { status, cached_days: cachedDays },
  activity: { events, capacity: 100 },
})

describe('SystemActivity', () => {
  it('is titled System Activity and never claims to be live', () => {
    render(<SystemActivity state={ready([event()])} />)

    expect(screen.getByRole('heading', { name: 'System Activity' })).toBeInTheDocument()
    expect(screen.queryByText(/\blive\b/i)).not.toBeInTheDocument()
  })

  it('lists the events it was given, with UTC times', () => {
    const match = event({
      id: 2,
      kind: 'match',
      message: '2026-01-15: 24 of 24 hours matched',
      details: { matched_hours: 24, expected_hours: 24 },
    })
    render(<SystemActivity state={ready([event(), match])} />)

    expect(screen.getByText('FUELHH 2026-01-15: 48 wind rows loaded')).toBeInTheDocument()
    expect(screen.getByText('2026-01-15: 24 of 24 hours matched')).toBeInTheDocument()
    expect(screen.getAllByText('16:33:08')).toHaveLength(2)
  })

  it('shows the cache status and day count from the ready data', () => {
    render(<SystemActivity state={ready([], 'warming', 0)} />)

    expect(screen.getByText('warming')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('explains an empty feed', () => {
    render(<SystemActivity state={ready([])} />)

    expect(screen.getByText(/no pipeline events yet/i)).toBeInTheDocument()
  })

  it('shows a warning when the feed cannot be loaded', () => {
    render(<SystemActivity state={{ status: 'error' }} />)

    expect(screen.getByRole('alert')).toHaveTextContent(/activity feed unavailable/i)
  })
})
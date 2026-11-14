import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Snapshot } from '../api/client'
import { MonthOverview } from './MonthOverview'

const metrics = (mae: number) => ({
  sample_count: 24,
  mae_mw: mae,
  rmse_mw: mae,
  bias_mw: mae,
})

const SNAPSHOT: Snapshot = {
  period: { start: '2026-01-02', end: '2026-02-01' },
  timezone: 'UTC',
  forecast_cutoff: {
    cutoff_utc: '09:50:00',
    policy: 'latest forecast published at or before 09:50:00 UTC on the previous calendar day',
  },
  coverage: { expected_hours: 744, matched_hours: 744, unmatched_hours: 0 },
  metrics: { sample_count: 744, mae_mw: 2013.008, rmse_mw: 2505.943, bias_mw: 1729.931 },
  error_percentiles: { p50: 1605.5, p90: 4145.5, p95: 5324.5, max: 6833 },
  daily: [
    { date: '2026-01-02', ...metrics(3196.2) },
    { date: '2026-01-03', ...metrics(2102.2) },
    { date: '2026-01-04', ...metrics(887.75) },
  ],
  hourly: [
    { hour: 0, ...metrics(1500) },
    { hour: 1, ...metrics(1700) },
  ],
  points: [],
  generated_at: '2026-11-10T13:55:24Z',
}

describe('MonthOverview', () => {
  it('shows the month-wide metrics and the signed bias', () => {
    render(<MonthOverview snapshot={SNAPSHOT} />)

    expect(screen.getByText('2,013 MW')).toBeInTheDocument()
    expect(screen.getByText('+1,730 MW')).toBeInTheDocument()
  })

  it('says it is a snapshot and when it was generated', () => {
    render(<MonthOverview snapshot={SNAPSHOT} />)

    expect(screen.getByText(/Snapshot generated 10 Nov 13:55 UTC/)).toBeInTheDocument()
    expect(screen.getByText(/02 Jan to 01 Feb/)).toBeInTheDocument()
  })

  it('names the worst days with their MAE', () => {
    render(<MonthOverview snapshot={SNAPSHOT} />)

    expect(
      screen.getByText('Worst days: 02 Jan (3,196 MW), 03 Jan (2,102 MW), 04 Jan (888 MW).'),
    ).toBeInTheDocument()
  })

  it('has both charts, labelled, and the error spread', () => {
    render(<MonthOverview snapshot={SNAPSHOT} />)

    expect(screen.getByRole('img', { name: /each delivery day/i })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /hour of day/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /how large the misses were/i })).toBeInTheDocument()
  })
})
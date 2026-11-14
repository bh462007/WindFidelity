import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('./components/GenerationChart', () => ({
  GenerationChart: () => <div data-testid="generation-chart" />,
}))
vi.mock('./components/ErrorChart', () => ({
  ErrorChart: () => <div data-testid="error-chart" />,
}))

const m = (mae: number, bias = mae) => ({
  sample_count: 24,
  mae_mw: mae,
  rmse_mw: mae,
  bias_mw: bias,
})

const SNAPSHOT = {
  period: { start: '2026-01-02', end: '2026-02-01' },
  timezone: 'UTC',
  forecast_cutoff: { cutoff_utc: '09:50:00', policy: 'policy text' },
  coverage: { expected_hours: 744, matched_hours: 744, unmatched_hours: 0 },
  metrics: { sample_count: 744, mae_mw: 2013.008, rmse_mw: 2505.943, bias_mw: 1729.931 },
  error_percentiles: { p50: 1605.5, p90: 4145.5, p95: 5324.5, max: 6833 },
  daily: [
    { date: '2026-01-02', ...m(3196.2) },
    { date: '2026-01-15', ...m(1189.79) },
  ],
  hourly: [{ hour: 0, ...m(1500) }],
  points: [
    {
      startTime: '2026-01-15T00:00:00Z',
      publishTime: '2026-01-14T09:30:00Z',
      forecast_mw: 15813,
      actual_mw: 14456.5,
    },
  ],
  generated_at: '2026-11-10T13:55:24Z',
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })

function routeFetch(handler: (url: string) => Response) {
  const fn = vi.fn((url: string, ..._rest: unknown[]) => {
    if (url.includes('/activity')) {
      return Promise.resolve(json({ events: [], capacity: 100 }))
    }
    if (url === '/ready') {
      return Promise.resolve(json({ status: 'warming', cached_days: 0 }))
    }
    return Promise.resolve(handler(url))
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

const healthy = () => json(SNAPSHOT)

afterEach(() => vi.unstubAllGlobals())

describe('App', () => {
  it('shows loading, then the January overview', async () => {
    routeFetch(healthy)
    render(<App />)

    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'MAE' })).toBeInTheDocument()
    expect(screen.getByText('+1,730 MW')).toBeInTheDocument()
    expect(screen.getByText(/Snapshot generated 10 Nov 13:55 UTC/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'System Activity' })).toBeInTheDocument()
  })

  it('shows "unavailable" and recovers when Retry is clicked', async () => {
    let backendUp = false
    routeFetch(() =>
      backendUp
        ? healthy()
        : json({ error: { code: 'snapshot_unavailable', message: 'down' } }, 503),
    )
    render(<App />)

    const retry = await screen.findByRole('button', { name: 'Retry' })
    expect(screen.getByRole('heading', { name: 'Data unavailable' })).toBeInTheDocument()

    backendUp = true
    await userEvent.click(retry)

    expect(await screen.findByRole('heading', { name: 'MAE' })).toBeInTheDocument()
  })

  it('switches to a single day and states which forecast was in force', async () => {
    routeFetch(healthy)
    render(<App />)
    await screen.findByRole('heading', { name: 'MAE' })

    await userEvent.click(screen.getByRole('button', { name: 'Single day' }))

    expect(screen.getByTestId('generation-chart')).toBeInTheDocument()
    expect(screen.getByTestId('error-chart')).toBeInTheDocument()
    expect(
      screen.getByText('Forecast in force at decision time: published 14 Jan 09:30 UTC.'),
    ).toBeInTheDocument()
  })

  it('limits the day picker to the snapshot period', async () => {
    routeFetch(healthy)
    render(<App />)
    await screen.findByRole('heading', { name: 'MAE' })

    await userEvent.click(screen.getByRole('button', { name: 'Single day' }))

    const picker = screen.getByLabelText(/delivery day/i)
    expect(picker).toHaveAttribute('min', '2026-01-02')
    expect(picker).toHaveAttribute('max', '2026-02-01')
  })

  it('shows "no data" for a day inside the period that has no points', async () => {
    routeFetch(healthy)
    render(<App />)
    await screen.findByRole('heading', { name: 'MAE' })
    await userEvent.click(screen.getByRole('button', { name: 'Single day' }))

    fireEvent.change(screen.getByLabelText(/delivery day/i), {
      target: { value: '2026-01-20' },
    })

    expect(await screen.findByRole('heading', { name: 'No data for this day' })).toBeInTheDocument()
  })
})
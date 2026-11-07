import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('./components/GenerationChart', () => ({
  GenerationChart: () => <div data-testid="generation-chart" />,
}))
vi.mock('./components/ErrorChart', () => ({
  ErrorChart: () => <div data-testid="error-chart" />,
}))

const SUMMARY = {
  date: '2026-01-15',
  timezone: 'UTC',
  forecast_cutoff: { cutoff_utc: '12:00:00', policy: 'policy text' },
  coverage: { expected_hours: 24, matched_hours: 24, unmatched_hours: 0 },
  metrics: { sample_count: 24, mae_mw: 1189.79, rmse_mw: 1289.02, bias_mw: 1189.79 },
}

const POINT = {
  startTime: '2026-01-15T00:00:00Z',
  publishTime: '2026-01-14T11:30:00Z',
  forecast_mw: 15813,
  actual_mw: 14456.5,
}

const SERIES = { date: '2026-01-15', timezone: 'UTC', points: [POINT] }

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

const healthy = (url: string) => json(url.includes('/summary') ? SUMMARY : SERIES)

afterEach(() => vi.unstubAllGlobals())

describe('App', () => {
  it('shows loading, then cards and both charts', async () => {
    routeFetch(healthy)
    render(<App />)

    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'MAE' })).toBeInTheDocument()
    expect(screen.getByText('+1,190 MW')).toBeInTheDocument()
    expect(screen.getByTestId('generation-chart')).toBeInTheDocument()
    expect(screen.getByTestId('error-chart')).toBeInTheDocument()
        expect(screen.getByRole('heading', { name: 'System Activity' })).toBeInTheDocument()
  })

  it('shows "no data" when the API reports no data', async () => {
    routeFetch(() => json({ error: { code: 'no_data', message: 'nothing' } }, 422))
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'No data for this day' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument()
  })

  it('shows "no data" when the series comes back empty', async () => {
    routeFetch((url) =>
      json(url.includes('/summary') ? SUMMARY : { ...SERIES, points: [] }),
    )
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'No data for this day' })).toBeInTheDocument()
  })

  it('shows "unavailable" and recovers when Retry is clicked', async () => {
    let backendUp = false
    routeFetch((url) =>
      backendUp
        ? healthy(url)
        : json({ error: { code: 'upstream_unavailable', message: 'Elexon down' } }, 503),
    )
    render(<App />)

    const retry = await screen.findByRole('button', { name: 'Retry' })
    expect(screen.getByRole('heading', { name: 'Data unavailable' })).toBeInTheDocument()

    backendUp = true
    await userEvent.click(retry)

    expect(await screen.findByRole('heading', { name: 'MAE' })).toBeInTheDocument()
  })

  it('fetches the new day when the date changes', async () => {
    const fn = routeFetch(healthy)
    render(<App />)
    await screen.findByRole('heading', { name: 'MAE' })

    fireEvent.change(screen.getByLabelText(/delivery day/i), {
      target: { value: '2026-01-20' },
    })

    await waitFor(() =>
      expect(fn).toHaveBeenCalledWith('/api/v1/summary?day=2026-01-20', expect.anything()),
    )
  })
})
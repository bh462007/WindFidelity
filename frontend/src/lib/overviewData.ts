import type { DailyMetrics, HourlyMetrics } from '../api/client'

export interface DailyRow {
  date: string
  MAE: number
  Bias: number
}

export interface HourlyRow {
  hour: string
  MAE: number
  Bias: number
}

/** "2026-01-02" -> "02 Jan". Pinned to UTC so the browser timezone cannot shift the day. */
export const dayLabel = (date: string) =>
  new Date(`${date}T00:00:00Z`).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    timeZone: 'UTC',
  })

export const dailyRows = (daily: DailyMetrics[]): DailyRow[] =>
  daily.map((d) => ({ date: d.date, MAE: Math.round(d.mae_mw), Bias: Math.round(d.bias_mw) }))

export const hourlyRows = (hourly: HourlyMetrics[]): HourlyRow[] =>
  hourly.map((h) => ({
    hour: `${String(h.hour).padStart(2, '0')}:00`,
    MAE: Math.round(h.mae_mw),
    Bias: Math.round(h.bias_mw),
  }))

export const worstDays = (daily: DailyMetrics[], count = 3): DailyMetrics[] =>
  [...daily].sort((a, b) => b.mae_mw - a.mae_mw).slice(0, count)
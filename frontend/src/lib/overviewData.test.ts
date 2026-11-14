import { describe, expect, it } from 'vitest'
import type { DailyMetrics, HourlyMetrics } from '../api/client'
import { dailyRows, dayLabel, hourlyRows, worstDays } from './overviewData'

const day = (date: string, mae: number, bias: number): DailyMetrics => ({
  date,
  sample_count: 24,
  mae_mw: mae,
  rmse_mw: mae,
  bias_mw: bias,
})

const hour = (h: number, mae: number, bias: number): HourlyMetrics => ({
  hour: h,
  sample_count: 31,
  mae_mw: mae,
  rmse_mw: mae,
  bias_mw: bias,
})

describe('dayLabel', () => {
  it('formats a UTC date without shifting it', () => {
    expect(dayLabel('2026-01-02')).toBe('02 Jan')
    expect(dayLabel('2026-02-01')).toBe('01 Feb')
  })
})

describe('dailyRows', () => {
  it('rounds to whole MW and keeps the date', () => {
    const rows = dailyRows([day('2026-01-02', 3196.2083, 3196.2083), day('2026-01-04', 887.75, -12.4)])

    expect(rows).toEqual([
      { date: '2026-01-02', MAE: 3196, Bias: 3196 },
      { date: '2026-01-04', MAE: 888, Bias: -12 },
    ])
  })
})

describe('hourlyRows', () => {
  it('labels hours as zero-padded UTC times', () => {
    const rows = hourlyRows([hour(0, 1500.4, 100), hour(13, 2100.6, -50.2)])

    expect(rows).toEqual([
      { hour: '00:00', MAE: 1500, Bias: 100 },
      { hour: '13:00', MAE: 2101, Bias: -50 },
    ])
  })
})

describe('worstDays', () => {
  it('returns the days with the largest MAE, worst first', () => {
    const days = [day('2026-01-02', 3196, 0), day('2026-01-03', 2102, 0), day('2026-01-04', 888, 0)]

    expect(worstDays(days, 2).map((d) => d.date)).toEqual(['2026-01-02', '2026-01-03'])
  })

  it('does not reorder the input', () => {
    const days = [day('2026-01-04', 888, 0), day('2026-01-02', 3196, 0)]

    worstDays(days, 1)

    expect(days.map((d) => d.date)).toEqual(['2026-01-04', '2026-01-02'])
  })
})
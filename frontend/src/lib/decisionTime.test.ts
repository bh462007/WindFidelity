import { describe, expect, it } from 'vitest'
import type { Point } from '../api/client'
import { forecastVintage, pointsForDay, publishLabel } from './decisionTime'

const point = (startTime: string, publishTime: string): Point => ({
  startTime,
  publishTime,
  forecast_mw: 100,
  actual_mw: 90,
})

const POINTS = [
  point('2026-01-02T00:00:00Z', '2026-01-01T09:30:00Z'),
  point('2026-01-02T01:00:00Z', '2026-01-01T09:30:00Z'),
  point('2026-01-03T00:00:00Z', '2026-01-02T09:30:00Z'),
]

describe('pointsForDay', () => {
  it('keeps only the points delivered on that UTC date', () => {
    expect(pointsForDay(POINTS, '2026-01-02')).toHaveLength(2)
    expect(pointsForDay(POINTS, '2026-01-03')).toHaveLength(1)
    expect(pointsForDay(POINTS, '2026-01-09')).toEqual([])
  })
})

describe('forecastVintage', () => {
  it('reports a single publication when every hour used the same one', () => {
    expect(forecastVintage(pointsForDay(POINTS, '2026-01-02'))).toEqual({
      first: '2026-01-01T09:30:00Z',
      last: '2026-01-01T09:30:00Z',
      count: 1,
    })
  })

  it('reports the span when hours used different publications', () => {
    const mixed = [
      point('2026-01-02T00:00:00Z', '2026-01-01T09:30:00Z'),
      point('2026-01-02T23:00:00Z', '2026-01-01T07:30:00Z'),
    ]

    expect(forecastVintage(mixed)).toEqual({
      first: '2026-01-01T07:30:00Z',
      last: '2026-01-01T09:30:00Z',
      count: 2,
    })
  })

  it('returns null for no points', () => {
    expect(forecastVintage([])).toBeNull()
  })
})

describe('publishLabel', () => {
  it('formats a publish time in UTC', () => {
    expect(publishLabel('2026-01-01T09:30:00Z')).toBe('01 Jan 09:30 UTC')
  })
})
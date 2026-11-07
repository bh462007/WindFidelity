import { describe, expect, it } from 'vitest'
import type { Point } from '../api/client'
import { MAX_RENDERED_POINTS, errorRows, generationRows } from './chartData'

const point = (i: number, forecast = 100, actual = 90): Point => ({
  startTime: new Date(Date.UTC(2026, 0, 1, 0, i)).toISOString(),
  publishTime: '2025-12-31T11:30:00Z',
  forecast_mw: forecast,
  actual_mw: actual,
})

const many = (n: number) => Array.from({ length: n }, (_, i) => point(i, 100 + (i % 7), 90))

describe('chart data', () => {
  it('keeps every point for a normal day', () => {
    expect(generationRows(many(24))).toHaveLength(24)
    expect(errorRows(many(24))).toHaveLength(24)
  })

  it('never renders more than the point cap', () => {
    expect(generationRows(many(5000))).toHaveLength(MAX_RENDERED_POINTS)
    expect(errorRows(many(5000))).toHaveLength(MAX_RENDERED_POINTS)
  })

  it('computes error as forecast minus actual', () => {
    expect(errorRows([point(0, 110, 100.4)])[0].Error).toBe(10)
    expect(errorRows([point(0, 80, 100)])[0].Error).toBe(-20)
  })

  it('keeps the largest miss when thinning', () => {
    const points = many(2000)
    points[1234] = point(1234, 5000, 90)

    expect(errorRows(points).some((row) => row.Error === 4910)).toBe(true)
  })
})
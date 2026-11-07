import type { Point } from '../api/client'
import { downsample } from './downsample'

export const MAX_RENDERED_POINTS = 500

export interface GenerationRow {
  t: string
  Actual: number
  Forecast: number
}

export interface ErrorRow {
  t: string
  Error: number
}

export function generationRows(points: Point[], max = MAX_RENDERED_POINTS): GenerationRow[] {
  const rows = points.map((p) => ({
    t: p.startTime,
    Actual: p.actual_mw,
    Forecast: p.forecast_mw,
  }))
  return downsample(rows, max, (row) => row.Actual)
}

export function errorRows(points: Point[], max = MAX_RENDERED_POINTS): ErrorRow[] {
  const rows = points.map((p) => ({
    t: p.startTime,
    Error: Math.round(p.forecast_mw - p.actual_mw),
  }))
  return downsample(rows, max, (row) => row.Error)
}
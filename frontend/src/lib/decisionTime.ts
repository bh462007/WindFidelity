import type { Point } from '../api/client'
import { dayLabel } from './overviewData'

export interface Vintage {
  first: string
  last: string
  count: number
}

/** Points whose delivery hour falls on the given UTC date (YYYY-MM-DD). */
export const pointsForDay = (points: Point[], day: string): Point[] =>
  points.filter((p) => p.startTime.startsWith(day))

/** Which forecast publications the points used: earliest, latest and how many distinct. */
export function forecastVintage(points: Point[]): Vintage | null {
  if (points.length === 0) return null

  const times = [...new Set(points.map((p) => p.publishTime))].sort()
  return { first: times[0], last: times[times.length - 1], count: times.length }
}

/** "2026-01-01T09:30:00Z" -> "01 Jan 09:30 UTC". */
export const publishLabel = (iso: string) => `${dayLabel(iso.slice(0, 10))} ${iso.slice(11, 16)} UTC`
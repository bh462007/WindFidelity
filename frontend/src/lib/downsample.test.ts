import { describe, expect, it } from 'vitest'
import { downsample } from './downsample'

const series = (n: number) =>
  Array.from({ length: n }, (_, i) => ({ i, v: Math.sin(i / 10) * 100 }))
const y = (p: { v: number }) => p.v

describe('downsample', () => {
  it('returns the input untouched when it is within the limit', () => {
    const data = series(24)

    expect(downsample(data, 500, y)).toBe(data)
  })

  it('reduces a long series to exactly the limit', () => {
    expect(downsample(series(5000), 500, y)).toHaveLength(500)
  })

  it('keeps the first and last points', () => {
    const data = series(5000)

    const result = downsample(data, 500, y)

    expect(result[0]).toBe(data[0])
    expect(result[result.length - 1]).toBe(data[data.length - 1])
  })

  it('returns original points only, in order, without repeats', () => {
    const indexes = downsample(series(2000), 100, y).map((p) => p.i)

    expect(indexes).toEqual([...indexes].sort((a, b) => a - b))
    expect(new Set(indexes).size).toBe(indexes.length)
  })

  it('keeps a single spike that averaging would hide', () => {
    const data = Array.from({ length: 1000 }, (_, i) => ({ i, v: i === 503 ? 1000 : 0 }))

    expect(downsample(data, 50, y).some((p) => p.v === 1000)).toBe(true)
  })

  it('rejects a limit too small to draw a line', () => {
    expect(() => downsample(series(10), 2, y)).toThrow(RangeError)
  })
})
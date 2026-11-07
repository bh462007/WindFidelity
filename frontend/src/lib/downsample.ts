/**
 * Largest-Triangle-Three-Buckets downsampling. Keeps the first and last points
 * and, in each bucket, the point that best preserves the visual shape, so peaks
 * and dips survive. Returns original items only.
 */
export function downsample<T>(items: T[], maxPoints: number, y: (item: T) => number): T[] {
  if (maxPoints < 3) throw new RangeError('maxPoints must be at least 3')
  if (items.length <= maxPoints) return items

  const sampled: T[] = [items[0]]
  const bucketSize = (items.length - 2) / (maxPoints - 2)
  let anchor = 0

  for (let i = 0; i < maxPoints - 2; i++) {
    const nextStart = Math.floor((i + 1) * bucketSize) + 1
    const nextEnd = Math.min(Math.floor((i + 2) * bucketSize) + 1, items.length)
    let avgX = 0
    let avgY = 0
    for (let j = nextStart; j < nextEnd; j++) {
      avgX += j
      avgY += y(items[j])
    }
    avgX /= nextEnd - nextStart
    avgY /= nextEnd - nextStart

    const start = Math.floor(i * bucketSize) + 1
    const end = Math.floor((i + 1) * bucketSize) + 1
    const anchorY = y(items[anchor])
    let maxArea = -1
    let chosen = start
    for (let j = start; j < end; j++) {
      const area = Math.abs(
        (anchor - avgX) * (y(items[j]) - anchorY) - (anchor - j) * (avgY - anchorY),
      )
      if (area > maxArea) {
        maxArea = area
        chosen = j
      }
    }

    sampled.push(items[chosen])
    anchor = chosen
  }

  sampled.push(items[items.length - 1])
  return sampled
}
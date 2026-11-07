export const axisStyle = {
  tick: { fill: 'var(--muted)', fontSize: 12 },
  axisLine: { stroke: 'var(--line)' },
  tickLine: { stroke: 'var(--line)' },
}

export const gridStyle = {
  stroke: 'var(--line)',
  strokeDasharray: '3 3',
}

export const tooltipStyle = {
  contentStyle: {
    background: 'var(--surface-raised)',
    border: '1px solid var(--line)',
    borderRadius: 6,
    color: 'var(--text)',
  },
  labelStyle: { color: 'var(--muted)' },
  itemStyle: { color: 'var(--text)' },
}

export const hourLabel = (t: string) => t.slice(11, 16)

export const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Point } from '../api/client'
import { generationRows } from '../lib/chartData'
import { axisStyle, gridStyle, hourLabel, prefersReducedMotion, tooltipStyle } from './chartTheme'

const formatMw = (value: unknown) => `${Math.round(Number(value)).toLocaleString('en-GB')} MW`

export function GenerationChart({ points }: { points: Point[] }) {
  const data = generationRows(points)
  const animate = !prefersReducedMotion()

  return (
    <section className="chart">
      <h2>Forecast vs actual generation</h2>
      <div role="img" aria-label="Line chart of forecast and actual wind generation by hour">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid {...gridStyle} />
            <XAxis dataKey="t" tickFormatter={hourLabel} {...axisStyle} />
            <YAxis
              width={80}
              domain={['auto', 'auto']}
              tickFormatter={(value: number) => value.toLocaleString('en-GB')}
              label={{ value: 'MW', angle: -90, position: 'insideLeft', fill: 'var(--muted)' }}
              {...axisStyle}
            />
            <Tooltip
              {...tooltipStyle}
              cursor={{ stroke: 'var(--muted)' }}
              labelFormatter={(t) => `${hourLabel(String(t))} UTC`}
              formatter={formatMw}
            />
            <Legend
              formatter={(value) => <span style={{ color: 'var(--text)' }}>{value}</span>}
            />
            <Line
              type="monotone"
              dataKey="Actual"
              stroke="var(--series-actual)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={animate}
            />
            <Line
              type="monotone"
              dataKey="Forecast"
              stroke="var(--series-forecast)"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={false}
              isAnimationActive={animate}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="caption">Hours are UTC.</p>
    </section>
  )
}
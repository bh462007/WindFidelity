import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Point } from '../api/client'
import { errorRows } from '../lib/chartData'
import { axisStyle, gridStyle, hourLabel, prefersReducedMotion, tooltipStyle } from './chartTheme'

function formatSignedMw(value: unknown) {
  const rounded = Math.round(Number(value))
  return `${rounded > 0 ? '+' : ''}${rounded.toLocaleString('en-GB')} MW`
}

export function ErrorChart({ points }: { points: Point[] }) {
  const data = errorRows(points)

  return (
    <section className="chart">
      <h2>Forecast error by hour</h2>
      <div role="img" aria-label="Bar chart of forecast minus actual generation by hour">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid {...gridStyle} />
            <XAxis dataKey="t" tickFormatter={hourLabel} {...axisStyle} />
            <YAxis
              width={80}
              tickFormatter={(value: number) => value.toLocaleString('en-GB')}
              label={{ value: 'MW', angle: -90, position: 'insideLeft', fill: 'var(--muted)' }}
              {...axisStyle}
            />
            <Tooltip
              {...tooltipStyle}
              cursor={{ fill: 'rgb(255 255 255 / 0.05)' }}
              labelFormatter={(t) => `${hourLabel(String(t))} UTC`}
              formatter={(value) => [formatSignedMw(value), 'Forecast − actual']}
            />
            <ReferenceLine y={0} stroke="var(--muted)" />
            <Bar dataKey="Error" isAnimationActive={!prefersReducedMotion()}>
              {data.map((row) => (
                <Cell key={row.t} fill={row.Error >= 0 ? 'var(--positive)' : 'var(--negative)'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="caption">
        Mint: forecast above actual. Rose: forecast below actual. Hours are UTC.
      </p>
    </section>
  )
}
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { HourlyMetrics } from '../api/client'
import { hourlyRows } from '../lib/overviewData'
import { axisStyle, gridStyle, prefersReducedMotion, tooltipStyle } from './chartTheme'

export function HourlyProfileChart({ hourly }: { hourly: HourlyMetrics[] }) {
  const rows = hourlyRows(hourly)
  const animate = !prefersReducedMotion()

  return (
    <section className="chart">
      <h2>Error by hour of day</h2>
      <div role="img" aria-label="Bar chart of mean absolute error by hour of day, pooled over the month">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid {...gridStyle} vertical={false} />
            <XAxis dataKey="hour" interval={2} {...axisStyle} />
            <YAxis
              width={80}
              tickFormatter={(value: number) => value.toLocaleString('en-GB')}
              label={{ value: 'MAE (MW)', angle: -90, position: 'insideLeft', fill: 'var(--muted)' }}
              {...axisStyle}
            />
            <Tooltip
              {...tooltipStyle}
              cursor={{ fill: 'var(--line)', opacity: 0.4 }}
              labelFormatter={(hour) => `${String(hour)} UTC`}
              formatter={(value) => `${Math.round(Number(value)).toLocaleString('en-GB')} MW`}
            />
            <Bar dataKey="MAE" fill="var(--series-actual)" isAnimationActive={animate} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="caption">Each bar pools the same hour across every day. Hours are UTC.</p>
    </section>
  )
}
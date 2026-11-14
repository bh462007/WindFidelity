import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { DailyMetrics } from '../api/client'
import { dailyRows, dayLabel, worstDays } from '../lib/overviewData'
import { axisStyle, gridStyle, prefersReducedMotion, tooltipStyle } from './chartTheme'

const formatMw = (value: number) => `${Math.round(value).toLocaleString('en-GB')} MW`

export function DailyMaeChart({ daily }: { daily: DailyMetrics[] }) {
  const rows = dailyRows(daily)
  const worst = worstDays(daily, 3)
  const worstDates = new Set(worst.map((d) => d.date))
  const animate = !prefersReducedMotion()

  return (
    <section className="chart">
      <h2>Daily error across the month</h2>
      <div role="img" aria-label="Bar chart of mean absolute error for each delivery day">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid {...gridStyle} vertical={false} />
            <XAxis dataKey="date" tickFormatter={dayLabel} interval={3} {...axisStyle} />
            <YAxis
              width={80}
              tickFormatter={(value: number) => value.toLocaleString('en-GB')}
              label={{ value: 'MAE (MW)', angle: -90, position: 'insideLeft', fill: 'var(--muted)' }}
              {...axisStyle}
            />
            <Tooltip
              {...tooltipStyle}
              cursor={{ fill: 'var(--line)', opacity: 0.4 }}
              labelFormatter={(date) => dayLabel(String(date))}
              formatter={(value) => formatMw(Number(value))}
            />
            <Bar dataKey="MAE" isAnimationActive={animate}>
              {rows.map((row) => (
                <Cell
                  key={row.date}
                  fill={worstDates.has(row.date) ? 'var(--warn, #F0A868)' : 'var(--series-actual)'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="caption">
        {`Worst days: ${worst.map((d) => `${dayLabel(d.date)} (${formatMw(d.mae_mw)})`).join(', ')}.`}
      </p>
    </section>
  )
}
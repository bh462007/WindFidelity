import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Point } from '../api/client'

function formatSignedMw(value: unknown) {
  const rounded = Math.round(Number(value))
  return `${rounded > 0 ? '+' : ''}${rounded.toLocaleString('en-GB')} MW`
}

export function ErrorChart({ points }: { points: Point[] }) {
  const data = points.map((p) => ({
    hour: p.startTime.slice(11, 16),
    Error: Math.round(p.forecast_mw - p.actual_mw),
  }))

  return (
    <section className="chart">
      <h2>Forecast error by hour</h2>
      <div role="img" aria-label="Bar chart of forecast minus actual generation by hour">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="hour" />
            <YAxis
              width={80}
              tickFormatter={(value: number) => value.toLocaleString('en-GB')}
              label={{ value: 'MW', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip formatter={formatSignedMw} />
            <ReferenceLine y={0} stroke="currentColor" />
            <Bar dataKey="Error" name="Forecast − actual" fill="#7c3aed" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="caption">
        Above zero: forecast higher than actual. Below zero: forecast lower. Hours are UTC.
      </p>
    </section>
  )
}
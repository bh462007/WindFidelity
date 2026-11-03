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

const formatMw = (value: unknown) => `${Math.round(Number(value)).toLocaleString('en-GB')} MW`

export function GenerationChart({ points }: { points: Point[] }) {
  const data = points.map((p) => ({
    hour: p.startTime.slice(11, 16),
    Forecast: p.forecast_mw,
    Actual: p.actual_mw,
  }))

  return (
    <section className="chart">
      <h2>Forecast vs actual generation</h2>
      <div role="img" aria-label="Line chart of forecast and actual wind generation by hour">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="hour" />
            <YAxis
              width={80}
              domain={['auto', 'auto']}
              tickFormatter={(value: number) => value.toLocaleString('en-GB')}
              label={{ value: 'MW', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip formatter={formatMw} />
            <Legend />
            <Line
              type="monotone"
              dataKey="Actual"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="Forecast"
              stroke="#ea580c"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="caption">Hours are UTC.</p>
    </section>
  )
}
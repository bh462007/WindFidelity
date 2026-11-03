import type { Summary } from '../api/client'

const formatMw = (value: number) => `${Math.round(value).toLocaleString('en-GB')} MW`

function formatSignedMw(value: number) {
  const rounded = Math.round(value)
  return `${rounded > 0 ? '+' : ''}${rounded.toLocaleString('en-GB')} MW`
}

function biasHint(value: number) {
  if (value > 0) return 'Forecast above actual on average'
  if (value < 0) return 'Forecast below actual on average'
  return 'No average bias'
}

interface CardProps {
  label: string
  value: string
  hint: string
}

function Card({ label, value, hint }: CardProps) {
  return (
    <section className="card">
      <h3>{label}</h3>
      <p className="value">{value}</p>
      <p className="hint">{hint}</p>
    </section>
  )
}

export function SummaryCards({ summary }: { summary: Summary }) {
  const { metrics, coverage, forecast_cutoff, timezone } = summary
  const coveragePct =
    coverage.expected_hours > 0
      ? Math.round((coverage.matched_hours / coverage.expected_hours) * 100)
      : 0

  return (
    <>
      <div className="cards">
        <Card label="MAE" value={formatMw(metrics.mae_mw)} hint="Average size of the miss" />
        <Card label="RMSE" value={formatMw(metrics.rmse_mw)} hint="Penalises large misses more" />
        <Card
          label="Bias"
          value={formatSignedMw(metrics.bias_mw)}
          hint={biasHint(metrics.bias_mw)}
        />
        <Card
          label="Coverage"
          value={`${coveragePct}%`}
          hint={`${coverage.matched_hours} of ${coverage.expected_hours} hours matched`}
        />
      </div>
      <p className="caption">
        {forecast_cutoff.policy} · times in {timezone}
      </p>
    </>
  )
}
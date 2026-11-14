import type { ErrorPercentiles } from '../api/client'

const formatMw = (value: number) => `${Math.round(value).toLocaleString('en-GB')} MW`

interface Props {
  percentiles: ErrorPercentiles
  hours: number
}

export function ErrorSpread({ percentiles, hours }: Props) {
  const rows: { label: string; hint: string; value: number }[] = [
    { label: 'Median miss', hint: 'Half of all hours were closer than this', value: percentiles.p50 },
    { label: '90th percentile', hint: '1 hour in 10 missed by more than this', value: percentiles.p90 },
    { label: '95th percentile', hint: '1 hour in 20 missed by more than this', value: percentiles.p95 },
    { label: 'Worst hour', hint: 'Largest single-hour miss', value: percentiles.max },
  ]

  return (
    <section className="chart">
      <h2>How large the misses were</h2>
      <dl className="spread">
        {rows.map((row) => (
          <div key={row.label}>
            <dt>
              {row.label}
              <span className="hint">{row.hint}</span>
            </dt>
            <dd>{formatMw(row.value)}</dd>
          </div>
        ))}
      </dl>
      <p className="caption">
        Absolute error (forecast minus actual, ignoring sign) across {hours.toLocaleString('en-GB')}{' '}
        hours.
      </p>
    </section>
  )
}
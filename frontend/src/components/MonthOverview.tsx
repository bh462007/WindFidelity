import type { Snapshot } from '../api/client'
import { dayLabel } from '../lib/overviewData'
import { publishLabel } from '../lib/decisionTime'
import { DailyMaeChart } from './DailyMaeChart'
import { ErrorSpread } from './ErrorSpread'
import { HourlyProfileChart } from './HourlyProfileChart'
import { SummaryCards } from './SummaryCards'

export function MonthOverview({ snapshot }: { snapshot: Snapshot }) {
  const { period, generated_at, coverage, error_percentiles, daily, hourly } = snapshot

  return (
    <>
      <SummaryCards summary={snapshot} />
      <p className="caption">
        {`Snapshot generated ${publishLabel(generated_at)} from Elexon data. Delivery days ${dayLabel(period.start)} to ${dayLabel(period.end)}.`}
      </p>
      <DailyMaeChart daily={daily} />
      <div className="pair">
        <HourlyProfileChart hourly={hourly} />
        <ErrorSpread percentiles={error_percentiles} hours={coverage.matched_hours} />
      </div>
    </>
  )
}
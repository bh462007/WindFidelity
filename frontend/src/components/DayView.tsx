import type { Snapshot } from '../api/client'
import { forecastVintage, pointsForDay, publishLabel } from '../lib/decisionTime'
import { ErrorChart } from './ErrorChart'
import { GenerationChart } from './GenerationChart'
import { ErrorState } from './States'
import { SummaryCards } from './SummaryCards'

interface Props {
  snapshot: Snapshot
  day: string
  onDayChange: (day: string) => void
}

function vintageNote(first: string, last: string, count: number) {
  if (count === 1) {
    return `Forecast in force at decision time: published ${publishLabel(first)}.`
  }
  return `Forecasts in force at decision time: published between ${publishLabel(first)} and ${publishLabel(last)} (${count} publications).`
}

export function DayView({ snapshot, day, onDayChange }: Props) {
  const points = pointsForDay(snapshot.points, day)
  const metrics = snapshot.daily.find((d) => d.date === day)
  const vintage = forecastVintage(points)

  const picker = (
    <label className="day-picker">
      Delivery day
      <input
        type="date"
        value={day}
        min={snapshot.period.start}
        max={snapshot.period.end}
        onChange={(e) => e.target.value && onDayChange(e.target.value)}
      />
    </label>
  )

  if (!metrics || !vintage) {
    return (
      <>
        {picker}
        <ErrorState kind="no_data" message="" onRetry={() => undefined} />
      </>
    )
  }

  return (
    <>
      {picker}
      <SummaryCards
        summary={{
          metrics,
          coverage: {
            expected_hours: 24,
            matched_hours: points.length,
            unmatched_hours: 24 - points.length,
          },
          forecast_cutoff: snapshot.forecast_cutoff,
          timezone: snapshot.timezone,
        }}
      />
      <p className="caption">{vintageNote(vintage.first, vintage.last, vintage.count)}</p>
      <GenerationChart points={points} />
      <ErrorChart points={points} />
    </>
  )
}
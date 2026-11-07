export interface Metrics {
  sample_count: number
  mae_mw: number
  rmse_mw: number
  bias_mw: number
}

export interface Coverage {
  expected_hours: number
  matched_hours: number
  unmatched_hours: number
}

export interface ForecastCutoff {
  cutoff_utc: string
  policy: string
}

export interface Summary {
  date: string
  timezone: string
  forecast_cutoff: ForecastCutoff
  coverage: Coverage
  metrics: Metrics
}

export interface Point {
  startTime: string
  publishTime: string
  forecast_mw: number
  actual_mw: number
}

export interface Timeseries {
  date: string
  timezone: string
  points: Point[]
}

export interface Ready {
  status: 'ready' | 'warming'
  cached_days: number
}

export type ActivityKind = 'ingestion' | 'match' | 'cache' | 'error'

export interface ActivityEvent {
  id: number
  timestamp: string
  kind: ActivityKind
  message: string
  details: Record<string, string | number>
}

export interface Activity {
  events: ActivityEvent[]
  capacity: number
}

export type ErrorKind = 'no_data' | 'unavailable' | 'invalid' | 'unknown'

export class ApiError extends Error {
  kind: ErrorKind

  constructor(kind: ErrorKind, message: string) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
  }
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, { signal })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError('unavailable', 'Cannot reach the API')
  }

  if (response.ok) return (await response.json()) as T

  let code = ''
  let message = `Request failed (${response.status})`
  try {
    const body = await response.json()
    code = body?.error?.code ?? ''
    message = body?.error?.message ?? message
  } catch {
    // Error body was not JSON (for example a proxy error page).
  }

  if (code === 'no_data') throw new ApiError('no_data', message)
  if (code === 'invalid_request') throw new ApiError('invalid', message)
  if (response.status >= 500) throw new ApiError('unavailable', message)
  throw new ApiError('unknown', message)
}

export const fetchSummary = (day: string, signal?: AbortSignal) =>
  getJson<Summary>(`/api/v1/summary?day=${encodeURIComponent(day)}`, signal)

export const fetchTimeseries = (day: string, signal?: AbortSignal) =>
  getJson<Timeseries>(`/api/v1/timeseries?day=${encodeURIComponent(day)}`, signal)

export const fetchReady = (signal?: AbortSignal) => getJson<Ready>('/ready', signal)

export const fetchActivity = (limit = 50, signal?: AbortSignal) =>
  getJson<Activity>(`/api/v1/activity?limit=${limit}`, signal)
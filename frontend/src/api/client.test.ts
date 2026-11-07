import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, fetchActivity, fetchReady, fetchSummary } from './client'


function mockFetch(outcome: Response | Error) {
    const fn = vi.fn((..._args: unknown[]) =>        outcome instanceof Response ? Promise.resolve(outcome) : Promise.reject(outcome),

  )
  vi.stubGlobal('fetch', fn)
  return fn
}

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })

afterEach(() => vi.unstubAllGlobals())

describe('api client', () => {
  it('returns parsed JSON on success', async () => {
    mockFetch(json({ date: '2026-01-15' }, 200))

    await expect(fetchSummary('2026-01-15')).resolves.toEqual({ date: '2026-01-15' })
  })

  it('requests the versioned summary URL for the chosen day', async () => {
    const fn = mockFetch(json({}, 200))

    await fetchSummary('2026-01-15')

    expect(fn.mock.calls[0][0]).toBe('/api/v1/summary?day=2026-01-15')
  })

  it('maps the no_data envelope to a no_data error', async () => {
    mockFetch(json({ error: { code: 'no_data', message: 'nothing found' } }, 422))

    const promise = fetchSummary('2027-01-01')

    await expect(promise).rejects.toBeInstanceOf(ApiError)
    await expect(promise).rejects.toMatchObject({ kind: 'no_data', message: 'nothing found' })
  })

  it('maps invalid_request to an invalid error', async () => {
    mockFetch(json({ error: { code: 'invalid_request', message: 'bad day' } }, 422))

    await expect(fetchSummary('x')).rejects.toMatchObject({ kind: 'invalid' })
  })

  it('maps the 503 envelope to an unavailable error', async () => {
    mockFetch(json({ error: { code: 'upstream_unavailable', message: 'Elexon down' } }, 503))

    await expect(fetchSummary('2026-01-15')).rejects.toMatchObject({
      kind: 'unavailable',
      message: 'Elexon down',
    })
  })

  it('treats a non-JSON 502 from the proxy as unavailable', async () => {
    mockFetch(new Response('Bad Gateway', { status: 502 }))

    await expect(fetchSummary('2026-01-15')).rejects.toMatchObject({ kind: 'unavailable' })
  })

  it('treats a network failure as unavailable', async () => {
    mockFetch(new TypeError('Failed to fetch'))

    await expect(fetchSummary('2026-01-15')).rejects.toMatchObject({ kind: 'unavailable' })
  })

  it('rethrows an aborted request untouched', async () => {
    mockFetch(new DOMException('aborted', 'AbortError'))

    await expect(fetchSummary('2026-01-15')).rejects.toMatchObject({ name: 'AbortError' })
  })
})

  it('requests the activity feed with a limit', async () => {
    const fn = mockFetch(json({ events: [], capacity: 100 }, 200))

    await fetchActivity(20)

    expect(fn.mock.calls[0][0]).toBe('/api/v1/activity?limit=20')
  })

  it('requests the ready endpoint', async () => {
    const fn = mockFetch(json({ status: 'warming', cached_days: 0 }, 200))

    await expect(fetchReady()).resolves.toEqual({ status: 'warming', cached_days: 0 })
    expect(fn.mock.calls[0][0]).toBe('/ready')
  })
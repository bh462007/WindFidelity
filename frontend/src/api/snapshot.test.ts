import { renderHook, waitFor, act } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fetchSnapshot } from './client'
import { useSnapshot } from '../hooks/useSnapshot'

const BODY = { generated_at: '2026-11-10T13:55:24Z', points: [] }

const okResponse = () => new Response(JSON.stringify(BODY), { status: 200 })
const unavailableResponse = () =>
  new Response(
    JSON.stringify({ error: { code: 'snapshot_unavailable', message: 'Snapshot is not available' } }),
    { status: 503 },
  )

afterEach(() => vi.unstubAllGlobals())

describe('fetchSnapshot', () => {
  it('requests the stored snapshot', async () => {
    const fetchMock = vi.fn((..._args: unknown[]) => Promise.resolve(okResponse()))
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchSnapshot()

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/snapshot')
    expect(result.generated_at).toBe(BODY.generated_at)
  })

  it('reports a 503 as unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn((..._args: unknown[]) => Promise.resolve(unavailableResponse())))

    await expect(fetchSnapshot()).rejects.toMatchObject({ kind: 'unavailable' })
  })
})

describe('useSnapshot', () => {
  it('goes from loading to ready', async () => {
    vi.stubGlobal('fetch', vi.fn((..._args: unknown[]) => Promise.resolve(okResponse())))

    const { result } = renderHook(() => useSnapshot())

    expect(result.current.state.status).toBe('loading')
    await waitFor(() => expect(result.current.state.status).toBe('ready'))
  })

  it('shows an error, then recovers on retry', async () => {
    let calls = 0
    vi.stubGlobal(
      'fetch',
      vi.fn((..._args: unknown[]) => {
        calls += 1
        return Promise.resolve(calls === 1 ? unavailableResponse() : okResponse())
      }),
    )

    const { result } = renderHook(() => useSnapshot())

    await waitFor(() => expect(result.current.state.status).toBe('error'))
    expect(result.current.state).toMatchObject({ kind: 'unavailable' })

    act(() => result.current.retry())

    await waitFor(() => expect(result.current.state.status).toBe('ready'))
  })
})
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ErrorState, Loading } from './States'

describe('States', () => {
  it('shows a loading status', () => {
    render(<Loading />)

    expect(screen.getByRole('status')).toHaveTextContent('Loading')
  })

  it('shows "no data" without a retry button', () => {
    render(<ErrorState kind="no_data" message="" onRetry={vi.fn()} />)

    expect(screen.getByRole('heading', { name: 'No data for this day' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument()
  })

  it('shows "unavailable" with a working retry button', async () => {
    const onRetry = vi.fn()
    render(<ErrorState kind="unavailable" message="Cannot reach the API" onRetry={onRetry} />)

    expect(screen.getByRole('heading', { name: 'Data unavailable' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))

    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('shows an invalid-date message without a retry button', () => {
    render(<ErrorState kind="invalid" message="bad day" onRetry={vi.fn()} />)

    expect(screen.getByRole('heading', { name: "That date isn't valid" })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument()
  })

  it('shows the reason a request failed', () => {
    render(<ErrorState kind="unavailable" message="Elexon down" onRetry={vi.fn()} />)

    expect(screen.getByText('Elexon down')).toBeInTheDocument()
  })
})
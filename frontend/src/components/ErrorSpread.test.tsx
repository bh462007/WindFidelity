import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ErrorSpread } from './ErrorSpread'


const PERCENTILES = { p50: 1605.5, p90: 4145.5, p95: 5324.5, max: 6833 }

describe('ErrorSpread', () => {
  it('shows each percentile in whole MW with a plain-words meaning', () => {
    render(<ErrorSpread percentiles={PERCENTILES} hours={744} />)

    expect(screen.getByText('1,606 MW')).toBeInTheDocument()
    expect(screen.getByText('4,146 MW')).toBeInTheDocument()
    expect(screen.getByText('5,325 MW')).toBeInTheDocument()
    expect(screen.getByText('6,833 MW')).toBeInTheDocument()
    expect(screen.getByText(/1 hour in 10/)).toBeInTheDocument()
    expect(screen.getByText(/1 hour in 20/)).toBeInTheDocument()
  })

  it('says how many hours the figures cover', () => {
    render(<ErrorSpread percentiles={PERCENTILES} hours={744} />)

    expect(screen.getByText(/744 hours/)).toBeInTheDocument()
  })

  it('has a heading for the panel', () => {
    render(<ErrorSpread percentiles={PERCENTILES} hours={744} />)

    expect(screen.getByRole('heading', { name: /how large the misses were/i })).toBeInTheDocument()
  })
})
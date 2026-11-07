import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Summary } from '../api/client'
import { SummaryCards } from './SummaryCards'

const summary = (bias: number, unmatched = 0): Summary => ({
  date: '2026-01-15',
  timezone: 'UTC',
  forecast_cutoff: { cutoff_utc: '12:00:00', policy: 'policy text' },
  coverage: {
    expected_hours: 24,
    matched_hours: 24 - unmatched,
    unmatched_hours: unmatched,
  },
  metrics: { sample_count: 24 - unmatched, mae_mw: 1000, rmse_mw: 1200, bias_mw: bias },
})

describe('SummaryCards', () => {
  it('marks a positive bias as positive', () => {
    render(<SummaryCards summary={summary(1190)} />)

    expect(screen.getByText('+1,190 MW')).toHaveClass('pos')
  })

  it('marks a negative bias as negative', () => {
    render(<SummaryCards summary={summary(-318)} />)

    expect(screen.getByText('-318 MW')).toHaveClass('neg')
  })

  it('gives a bias that rounds to zero no sign colour', () => {
    render(<SummaryCards summary={summary(0.3)} />)

    const value = screen.getByText('0 MW')
    expect(value).not.toHaveClass('pos')
    expect(value).not.toHaveClass('neg')
  })

  it('flags partial coverage as a warning', () => {
    render(<SummaryCards summary={summary(100, 1)} />)

    expect(screen.getByText('23 of 24 hours matched')).toHaveClass('warn')
  })

  it('does not warn when every hour matched', () => {
    render(<SummaryCards summary={summary(100)} />)

    expect(screen.getByText('24 of 24 hours matched')).not.toHaveClass('warn')
  })
})
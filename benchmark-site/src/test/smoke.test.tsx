/**
 * Smoke tests for the benchmark-site application.
 *
 * These tests verify that core components and modules can be imported
 * and that the basic application structure is intact.
 */

import { describe, it, expect } from 'vitest'

describe('Benchmark Site Smoke Tests', () => {
  describe('Module Imports', () => {
    it('should import React', async () => {
      const React = await import('react')
      expect(React).toBeDefined()
      expect(React.createElement).toBeDefined()
    })

    it('should import Next.js Link', async () => {
      const { default: Link } = await import('next/link')
      expect(Link).toBeDefined()
    })
  })

  describe('Environment', () => {
    it('should have jsdom environment', () => {
      expect(typeof window).toBe('object')
      expect(typeof document).toBe('object')
    })

    it('should have document.createElement', () => {
      const div = document.createElement('div')
      expect(div).toBeInstanceOf(HTMLDivElement)
    })
  })

  describe('Testing Library', () => {
    it('should render basic element', async () => {
      const { render, screen } = await import('@testing-library/react')
      const React = await import('react')

      render(React.createElement('div', { 'data-testid': 'test' }, 'Hello'))

      expect(screen.getByTestId('test')).toBeInTheDocument()
      expect(screen.getByText('Hello')).toBeInTheDocument()
    })
  })
})

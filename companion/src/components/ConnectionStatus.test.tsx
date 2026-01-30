/**
 * Tests for the ConnectionStatus component.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ConnectionStatus } from './ConnectionStatus'
import type { FleetStatePayload } from '@/lib/postMessageProtocol'

describe('ConnectionStatus', () => {
  describe('when connected', () => {
    it('should display connected status', () => {
      render(<ConnectionStatus isConnected={true} fleetState={null} />)

      expect(screen.getByText('Connected to Star Forge')).toBeInTheDocument()
    })

    it('should display fleet state when available', () => {
      const fleetState: FleetStatePayload = {
        faction: 'empire',
        points: { total: 250, ships: 200, squadrons: 50 },
        pointsLimit: 400,
        ships: [],
        squadrons: [],
      }

      render(<ConnectionStatus isConnected={true} fleetState={fleetState} />)

      expect(screen.getByText('Connected to Star Forge')).toBeInTheDocument()
      expect(screen.getByText(/empire/i)).toBeInTheDocument()
      expect(screen.getByText(/250\/400 pts/)).toBeInTheDocument()
    })

    it('should display "No faction" when faction is not set', () => {
      const fleetState: FleetStatePayload = {
        faction: null,
        points: { total: 0, ships: 0, squadrons: 0 },
        pointsLimit: 400,
        ships: [],
        squadrons: [],
      }

      render(<ConnectionStatus isConnected={true} fleetState={fleetState} />)

      expect(screen.getByText(/No faction/)).toBeInTheDocument()
    })

    it('should have green background styling when connected', () => {
      const { container } = render(
        <ConnectionStatus isConnected={true} fleetState={null} />
      )

      const statusDiv = container.firstChild as HTMLElement
      expect(statusDiv.className).toContain('bg-green')
    })
  })

  describe('when disconnected', () => {
    it('should display disconnected status', () => {
      render(<ConnectionStatus isConnected={false} fleetState={null} />)

      expect(
        screen.getByText('Not connected - Open from Star Forge')
      ).toBeInTheDocument()
    })

    it('should have yellow background styling when disconnected', () => {
      const { container } = render(
        <ConnectionStatus isConnected={false} fleetState={null} />
      )

      const statusDiv = container.firstChild as HTMLElement
      expect(statusDiv.className).toContain('bg-yellow')
    })

    it('should not display fleet state even if provided', () => {
      const fleetState: FleetStatePayload = {
        faction: 'rebel',
        points: { total: 300, ships: 200, squadrons: 100 },
        pointsLimit: 400,
        ships: [],
        squadrons: [],
      }

      render(<ConnectionStatus isConnected={false} fleetState={fleetState} />)

      // Fleet state should not be visible when disconnected
      expect(screen.queryByText(/rebel/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/300\/400/)).not.toBeInTheDocument()
    })
  })
})

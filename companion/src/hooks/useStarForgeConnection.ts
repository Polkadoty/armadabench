/**
 * useStarForgeConnection - Hook for connecting to Star Forge fleet builder
 *
 * Manages postMessage communication with the parent Star Forge window.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  FleetStatePayload,
  CompanionToStarForge,
  StarForgeToCompanion,
  ActionResult,
  generateMessageId,
} from '@/lib/postMessageProtocol';

// ============================================================================
// Allowed Origins (Star Forge domains)
// ============================================================================

const ALLOWED_ORIGINS = [
  'https://star-forge.tools',
  'https://www.star-forge.tools',
  'https://legacy.swarmada.wiki',
  'http://localhost:3000', // Next.js dev
  'http://127.0.0.1:3000',
];

// ============================================================================
// Hook Return Type
// ============================================================================

export interface UseStarForgeConnection {
  isConnected: boolean;
  fleetState: FleetStatePayload | null;

  // Fleet actions
  addShip: (shipId: string) => Promise<ActionResult>;
  removeShip: (instanceId: string) => Promise<ActionResult>;
  addUpgrade: (shipInstanceId: string, upgradeId: string) => Promise<ActionResult>;
  removeUpgrade: (shipInstanceId: string, upgradeId: string) => Promise<ActionResult>;
  addSquadron: (squadronId: string, count?: number) => Promise<ActionResult>;
  removeSquadron: (instanceId: string) => Promise<ActionResult>;
  setObjective: (type: 'assault' | 'defense' | 'navigation', objectiveId: string) => Promise<ActionResult>;
  setFleetName: (name: string) => Promise<ActionResult>;
  resetFleet: () => Promise<ActionResult>;
  requestFleetState: () => Promise<FleetStatePayload>;
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useStarForgeConnection(): UseStarForgeConnection {
  const [isConnected, setIsConnected] = useState(false);
  const [fleetState, setFleetState] = useState<FleetStatePayload | null>(null);

  const starForgeOriginRef = useRef<string | null>(null);
  const pendingRequestsRef = useRef<Map<string, {
    resolve: (value: ActionResult | FleetStatePayload) => void;
    reject: (error: Error) => void;
    timeout: ReturnType<typeof setTimeout>;
  }>>(new Map());

  // ============================================================================
  // Send Message to Star Forge
  // ============================================================================

  // Store reference to Star Forge window (either opener or message source)
  const starForgeWindowRef = useRef<Window | null>(null);
  // Store reference to BroadcastChannel for cross-tab communication
  const broadcastChannelRef = useRef<BroadcastChannel | null>(null);

  const sendToStarForge = useCallback((message: CompanionToStarForge): void => {
    // Prefer postMessage if we have a direct window connection (popup scenario)
    // This is more reliable than BroadcastChannel for bidirectional communication
    const targetWindow = starForgeWindowRef.current || window.opener;
    if (targetWindow && starForgeOriginRef.current) {
      try {
        console.log('[Companion] Sending via postMessage:', message.type);
        targetWindow.postMessage(message, starForgeOriginRef.current);
        return;
      } catch (error) {
        console.error('[Companion] Failed to send via postMessage:', error);
      }
    }

    // Fallback to BroadcastChannel (for cross-tab communication without popup)
    if (broadcastChannelRef.current) {
      try {
        console.log('[Companion] Sending via BroadcastChannel:', message.type);
        broadcastChannelRef.current.postMessage(message);
        return;
      } catch (error) {
        console.error('[Companion] Failed to send via BroadcastChannel:', error);
      }
    }

    console.warn('[Companion] Cannot send - not connected to Star Forge');
  }, []);

  // ============================================================================
  // Request with Response
  // ============================================================================

  const sendRequest = useCallback(<T extends ActionResult | FleetStatePayload>(
    message: CompanionToStarForge,
    timeoutMs = 10000
  ): Promise<T> => {
    return new Promise((resolve, reject) => {
      const id = message.id;

      // Set up timeout
      const timeout = setTimeout(() => {
        pendingRequestsRef.current.delete(id);
        reject(new Error('Request timed out'));
      }, timeoutMs);

      // Store pending request
      pendingRequestsRef.current.set(id, {
        resolve: resolve as (value: ActionResult | FleetStatePayload) => void,
        reject,
        timeout,
      });

      // Send message
      sendToStarForge(message);
    });
  }, [sendToStarForge]);

  // ============================================================================
  // Handle Incoming Messages
  // ============================================================================

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Validate origin
      if (!ALLOWED_ORIGINS.includes(event.origin)) {
        return;
      }

      const message = event.data as StarForgeToCompanion;
      if (!message || typeof message.type !== 'string') {
        return;
      }

      console.log('[Companion] Received:', message.type);

      switch (message.type) {
        case 'STAR_FORGE_READY':
          starForgeOriginRef.current = event.origin;
          starForgeWindowRef.current = event.source as Window;
          setIsConnected(true);
          console.log('[Companion] Connected to Star Forge at:', event.origin);
          break;

        case 'FLEET_STATE': {
          setFleetState(message.payload);
          const pending = pendingRequestsRef.current.get(message.requestId);
          if (pending) {
            clearTimeout(pending.timeout);
            pending.resolve(message.payload);
            pendingRequestsRef.current.delete(message.requestId);
          }
          break;
        }

        case 'ACTION_SUCCESS': {
          const pending = pendingRequestsRef.current.get(message.requestId);
          if (pending) {
            clearTimeout(pending.timeout);
            pending.resolve({ success: true, payload: message.payload });
            pendingRequestsRef.current.delete(message.requestId);
          }
          break;
        }

        case 'ACTION_ERROR': {
          const pending = pendingRequestsRef.current.get(message.requestId);
          if (pending) {
            clearTimeout(pending.timeout);
            pending.resolve({ success: false, error: message.error });
            pendingRequestsRef.current.delete(message.requestId);
          }
          break;
        }

        case 'FLEET_CHANGED':
          setFleetState(message.payload);
          break;
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  // ============================================================================
  // BroadcastChannel for cross-tab communication (fallback)
  // ============================================================================

  useEffect(() => {
    // Set up BroadcastChannel for cross-tab communication
    const channel = new BroadcastChannel('star-forge-companion');
    broadcastChannelRef.current = channel;

    channel.onmessage = (event) => {
      const message = event.data;
      if (!message || typeof message.type !== 'string') return;

      console.log('[Companion] BroadcastChannel received:', message.type);

      if (message.type === 'STAR_FORGE_READY') {
        starForgeOriginRef.current = message.origin || '*';
        setIsConnected(true);
        console.log('[Companion] Connected via BroadcastChannel');

        // Send confirmation back
        channel.postMessage({ type: 'COMPANION_CONNECTED', id: generateMessageId() });
      }

      // Handle fleet state updates
      if (message.type === 'FLEET_STATE') {
        console.log('[Companion] Received FLEET_STATE:', message.payload?.faction);
        setFleetState(message.payload);
        const pending = pendingRequestsRef.current.get(message.requestId);
        if (pending) {
          clearTimeout(pending.timeout);
          pending.resolve(message.payload);
          pendingRequestsRef.current.delete(message.requestId);
        }
      }

      if (message.type === 'FLEET_CHANGED') {
        console.log('[Companion] Received FLEET_CHANGED');
        setFleetState(message.payload);
      }

      if (message.type === 'ACTION_SUCCESS') {
        const pending = pendingRequestsRef.current.get(message.requestId);
        if (pending) {
          clearTimeout(pending.timeout);
          pending.resolve({ success: true, payload: message.payload });
          pendingRequestsRef.current.delete(message.requestId);
        }
      }

      if (message.type === 'ACTION_ERROR') {
        const pending = pendingRequestsRef.current.get(message.requestId);
        if (pending) {
          clearTimeout(pending.timeout);
          pending.resolve({ success: false, error: message.error });
          pendingRequestsRef.current.delete(message.requestId);
        }
      }
    };

    // Announce ourselves via BroadcastChannel after setting up listener
    // Small delay to ensure Star Forge's listener is ready
    const announceTimeout = setTimeout(() => {
      console.log('[Companion] Announcing via BroadcastChannel');
      channel.postMessage({ type: 'COMPANION_READY', id: generateMessageId() });
    }, 100);

    return () => {
      clearTimeout(announceTimeout);
      broadcastChannelRef.current = null;
      channel.close();
    };
  }, []);

  // ============================================================================
  // Announce Companion Ready via postMessage (for popup scenarios)
  // ============================================================================

  useEffect(() => {
    // If opened as a popup, announce ourselves to the opener
    if (window.opener) {
      // Try each allowed origin (we don't know which one opened us yet)
      ALLOWED_ORIGINS.forEach(origin => {
        try {
          window.opener.postMessage({ type: 'COMPANION_READY', id: generateMessageId() }, origin);
        } catch {
          // Ignore errors for wrong origins
        }
      });
    }
  }, []);

  // ============================================================================
  // Fleet Actions
  // ============================================================================

  const addShip = useCallback(async (shipId: string): Promise<ActionResult> => {
    return sendRequest<ActionResult>({
      type: 'ADD_SHIP',
      id: generateMessageId(),
      payload: { shipId },
    });
  }, [sendRequest]);

  const removeShip = useCallback(async (instanceId: string): Promise<ActionResult> => {
    return sendRequest<ActionResult>({
      type: 'REMOVE_SHIP',
      id: generateMessageId(),
      payload: { instanceId },
    });
  }, [sendRequest]);

  const addUpgrade = useCallback(async (
    shipInstanceId: string,
    upgradeId: string
  ): Promise<ActionResult> => {
    return sendRequest<ActionResult>({
      type: 'ADD_UPGRADE',
      id: generateMessageId(),
      payload: { shipInstanceId, upgradeId },
    });
  }, [sendRequest]);

  const removeUpgrade = useCallback(async (
    shipInstanceId: string,
    upgradeId: string
  ): Promise<ActionResult> => {
    return sendRequest<ActionResult>({
      type: 'REMOVE_UPGRADE',
      id: generateMessageId(),
      payload: { shipInstanceId, upgradeId },
    });
  }, [sendRequest]);

  const addSquadron = useCallback(async (
    squadronId: string,
    count?: number
  ): Promise<ActionResult> => {
    return sendRequest<ActionResult>({
      type: 'ADD_SQUADRON',
      id: generateMessageId(),
      payload: { squadronId, count },
    });
  }, [sendRequest]);

  const removeSquadron = useCallback(async (instanceId: string): Promise<ActionResult> => {
    return sendRequest<ActionResult>({
      type: 'REMOVE_SQUADRON',
      id: generateMessageId(),
      payload: { instanceId },
    });
  }, [sendRequest]);

  const setObjective = useCallback(async (
    type: 'assault' | 'defense' | 'navigation',
    objectiveId: string
  ): Promise<ActionResult> => {
    return sendRequest<ActionResult>({
      type: 'SET_OBJECTIVE',
      id: generateMessageId(),
      payload: { objectiveType: type, objectiveId },
    });
  }, [sendRequest]);

  const setFleetName = useCallback(async (name: string): Promise<ActionResult> => {
    return sendRequest<ActionResult>({
      type: 'SET_FLEET_NAME',
      id: generateMessageId(),
      payload: { name },
    });
  }, [sendRequest]);

  const resetFleet = useCallback(async (): Promise<ActionResult> => {
    return sendRequest<ActionResult>({
      type: 'RESET_FLEET',
      id: generateMessageId(),
    });
  }, [sendRequest]);

  const requestFleetState = useCallback(async (): Promise<FleetStatePayload> => {
    return sendRequest<FleetStatePayload>({
      type: 'REQUEST_FLEET_STATE',
      id: generateMessageId(),
    });
  }, [sendRequest]);

  return {
    isConnected,
    fleetState,
    addShip,
    removeShip,
    addUpgrade,
    removeUpgrade,
    addSquadron,
    removeSquadron,
    setObjective,
    setFleetName,
    resetFleet,
    requestFleetState,
  };
}

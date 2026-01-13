/**
 * postMessage Protocol Types
 *
 * Defines the message types for communication between the Companion app
 * and Star Forge fleet builder.
 */

// ============================================================================
// Fleet State
// ============================================================================

export interface FleetStatePayload {
  faction: string;
  gamemode: string;
  pointsLimit: number;
  points: {
    total: number;
    ships: number;
    squadrons: number;
  };
  // Gamemode restrictions
  restrictions: {
    squadronPointsLimit: number;
    flotillaLimit: number;
    aceLimit: number;
    requireCommander: boolean;
    requireObjectives: boolean;
  };
  // Current fleet status against restrictions
  status: {
    aceCount: number;
    flotillaCount: number;
    commanderCount: number;
    violations: string[];
  };
  ships: Array<{
    instanceId: string;
    id: string;
    name: string;
    points: number;
    upgrades: Array<{
      id: string;
      name: string;
      points: number;
      type: string;
    }>;
    availableSlots: string[];
  }>;
  squadrons: Array<{
    instanceId: string;
    id: string;
    name: string;
    points: number;
    count: number;
    unique: boolean;
    ace: boolean;
  }>;
  objectives: {
    assault: string | null;
    defense: string | null;
    navigation: string | null;
  };
  // Fleet text export for easy reading
  fleetText: string;
}

// ============================================================================
// Messages FROM Companion TO Star Forge
// ============================================================================

export type CompanionToStarForge =
  | { type: 'COMPANION_READY'; id: string }
  | { type: 'REQUEST_FLEET_STATE'; id: string }
  | { type: 'ADD_SHIP'; id: string; payload: { shipId: string } }
  | { type: 'REMOVE_SHIP'; id: string; payload: { instanceId: string } }
  | { type: 'ADD_UPGRADE'; id: string; payload: { shipInstanceId: string; upgradeId: string } }
  | { type: 'REMOVE_UPGRADE'; id: string; payload: { shipInstanceId: string; upgradeId: string } }
  | { type: 'ADD_SQUADRON'; id: string; payload: { squadronId: string; count?: number } }
  | { type: 'REMOVE_SQUADRON'; id: string; payload: { instanceId: string } }
  | { type: 'SET_OBJECTIVE'; id: string; payload: { objectiveType: 'assault' | 'defense' | 'navigation'; objectiveId: string } }
  | { type: 'SET_FLEET_NAME'; id: string; payload: { name: string } }
  | { type: 'RESET_FLEET'; id: string };

// ============================================================================
// Messages FROM Star Forge TO Companion
// ============================================================================

export type StarForgeToCompanion =
  | { type: 'STAR_FORGE_READY' }
  | { type: 'FLEET_STATE'; requestId: string; payload: FleetStatePayload }
  | { type: 'ACTION_SUCCESS'; requestId: string; payload?: unknown }
  | { type: 'ACTION_ERROR'; requestId: string; error: string }
  | { type: 'FLEET_CHANGED'; payload: FleetStatePayload };

// ============================================================================
// Action Result
// ============================================================================

export interface ActionResult {
  success: boolean;
  error?: string;
  payload?: unknown;
}

// ============================================================================
// Utilities
// ============================================================================

let messageIdCounter = 0;

export function generateMessageId(): string {
  return `msg_${Date.now()}_${++messageIdCounter}`;
}

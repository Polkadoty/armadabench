/**
 * Tool Executor
 *
 * Executes tool calls from the LLM, routing them to the appropriate handlers.
 */

import type { ParsedToolCall } from './openrouter';
import type { UseStarForgeConnection } from '@/hooks/useStarForgeConnection';
import { ISB_API_URL } from './tools';

// ============================================================================
// Types
// ============================================================================

export interface ToolExecutionResult {
  toolCallId: string;
  toolName: string;
  result: unknown;
  error?: string;
}

// ============================================================================
// ISB API Calls
// ============================================================================

async function searchCards(args: Record<string, unknown>): Promise<unknown> {
  const params = new URLSearchParams();

  if (args.query) params.set('query', String(args.query));
  if (args.type) params.set('type', String(args.type));
  if (args.faction) params.set('faction', String(args.faction));
  if (args.points) params.set('points', String(args.points));
  if (args.limit) params.set('limit', String(args.limit));

  const response = await fetch(`${ISB_API_URL}/search?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Search failed: ${response.status}`);
  }

  return response.json();
}

async function getCardDetails(cardId: string): Promise<unknown> {
  const response = await fetch(`${ISB_API_URL}/cards/${encodeURIComponent(cardId)}`);
  if (!response.ok) {
    if (response.status === 404) {
      return { error: `Card not found: ${cardId}` };
    }
    throw new Error(`Card lookup failed: ${response.status}`);
  }

  return response.json();
}

async function validateFleet(fleetState: unknown): Promise<unknown> {
  // Build fleet object from current state for validation
  const response = await fetch(`${ISB_API_URL}/validate-fleet`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fleetState),
  });

  if (!response.ok) {
    throw new Error(`Validation failed: ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// Tool Executor
// ============================================================================

export async function executeToolCall(
  toolCall: ParsedToolCall,
  starForge: UseStarForgeConnection
): Promise<ToolExecutionResult> {
  const { id, name, arguments: args } = toolCall;

  console.log(`[ToolExecutor] Executing: ${name}`, args);

  try {
    let result: unknown;

    switch (name) {
      // === READ OPERATIONS (ISB API) ===
      case 'search_cards':
        result = await searchCards(args);
        // Log search results count
        const searchResult = result as { results?: unknown[] };
        console.log(`[ToolExecutor] search_cards returned ${searchResult?.results?.length || 0} results`);
        break;

      case 'get_card_details':
        result = await getCardDetails(String(args.cardId));
        break;

      case 'get_fleet_state':
        // Always request fresh state from Star Forge to avoid stale React state
        console.log('[ToolExecutor] get_fleet_state - requesting fresh state from Star Forge');
        result = await starForge.requestFleetState();
        console.log('[ToolExecutor] get_fleet_state - received:', {
          faction: (result as { faction?: string })?.faction,
          ships: (result as { ships?: unknown[] })?.ships?.length,
          squadrons: (result as { squadrons?: unknown[] })?.squadrons?.length,
          points: (result as { points?: unknown })?.points,
        });
        break;

      case 'validate_fleet':
        // For now, just return the current fleet state
        // Full validation would need to format it for the ISB API
        if (starForge.fleetState) {
          result = await validateFleet({
            faction: starForge.fleetState.faction,
            ships: starForge.fleetState.ships.map(s => ({
              id: s.id,
              upgrades: s.upgrades.map(u => u.id),
            })),
            squadrons: starForge.fleetState.squadrons.map(s => ({
              id: s.id,
              count: s.count,
            })),
            points_limit: starForge.fleetState.pointsLimit,
          });
        } else {
          result = { error: 'No fleet state available' };
        }
        break;

      // === WRITE OPERATIONS (Star Forge postMessage) ===
      case 'add_ship':
        result = await starForge.addShip(String(args.shipId));
        break;

      case 'remove_ship':
        result = await starForge.removeShip(String(args.shipInstanceId));
        break;

      case 'add_upgrade':
        console.log(`[ToolExecutor] add_upgrade - shipInstanceId: ${args.shipInstanceId}, upgradeId: ${args.upgradeId}`);
        result = await starForge.addUpgrade(
          String(args.shipInstanceId),
          String(args.upgradeId)
        );
        console.log(`[ToolExecutor] add_upgrade result:`, result);
        break;

      case 'remove_upgrade':
        result = await starForge.removeUpgrade(
          String(args.shipInstanceId),
          String(args.upgradeId)
        );
        break;

      case 'add_squadron':
        result = await starForge.addSquadron(
          String(args.squadronId),
          args.count ? Number(args.count) : undefined
        );
        break;

      case 'remove_squadron':
        result = await starForge.removeSquadron(String(args.squadronInstanceId));
        break;

      case 'set_objective':
        result = await starForge.setObjective(
          args.objectiveType as 'assault' | 'defense' | 'navigation',
          String(args.objectiveId)
        );
        break;

      case 'reset_fleet':
        result = await starForge.resetFleet();
        break;

      case 'random_faction': {
        const factions = ['empire', 'rebel', 'republic', 'separatist'];
        const randomIndex = Math.floor(Math.random() * factions.length);
        const selectedFaction = factions[randomIndex];
        result = {
          success: true,
          faction: selectedFaction,
          message: `Randomly selected: ${selectedFaction.charAt(0).toUpperCase() + selectedFaction.slice(1)}`,
        };
        break;
      }

      case 'navigate_to_faction':
        if (starForge.navigateToFaction) {
          result = await starForge.navigateToFaction(String(args.faction));
        } else {
          result = { error: 'Navigate to faction not supported - please navigate manually' };
        }
        break;

      default:
        result = { error: `Unknown tool: ${name}` };
    }

    return { toolCallId: id, toolName: name, result };
  } catch (error) {
    return {
      toolCallId: id,
      toolName: name,
      result: null,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

// ============================================================================
// Execute Multiple Tool Calls
// ============================================================================

export async function executeToolCalls(
  toolCalls: ParsedToolCall[],
  starForge: UseStarForgeConnection
): Promise<ToolExecutionResult[]> {
  // Execute tool calls sequentially to avoid race conditions
  const results: ToolExecutionResult[] = [];

  for (const toolCall of toolCalls) {
    const result = await executeToolCall(toolCall, starForge);
    results.push(result);
  }

  return results;
}

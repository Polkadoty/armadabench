/**
 * useLLMChat - Hook for managing LLM conversation state
 *
 * Handles the agentic loop: sending messages, executing tool calls,
 * and building conversation history.
 */

import { useCallback, useState } from 'react';
import {
  Message,
  ParsedToolCall,
  chatWithOpenRouter,
  formatToolResult,
  formatAssistantToolCalls,
} from '@/lib/openrouter';
import { FLEET_BUILDING_TOOLS } from '@/lib/tools';
import { executeToolCalls, ToolExecutionResult } from '@/lib/toolExecutor';
import type { UseStarForgeConnection } from './useStarForgeConnection';
import type { FleetStatePayload } from '@/lib/postMessageProtocol';

// ============================================================================
// Types
// ============================================================================

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  toolCalls?: ParsedToolCall[];
  toolResults?: ToolExecutionResult[];
  timestamp: Date;
  isStreaming?: boolean;
}

export interface UseLLMChatOptions {
  apiKey: string;
  model: string;
  starForge: UseStarForgeConnection;
}

export interface UseLLMChat {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  clearHistory: () => void;
}

// ============================================================================
// System Prompt Builder
// ============================================================================

function buildSystemPrompt(fleetState: FleetStatePayload | null): string {
  let context: string;
  let restrictionsInfo = '';
  let statusInfo = '';
  let fleetTextInfo = '';

  if (fleetState) {
    context = `
## Current Fleet Context
- Faction: ${fleetState.faction || 'Not selected'}
- Game Mode: ${fleetState.gamemode || 'Standard'}
- Points: ${fleetState.points.total}/${fleetState.pointsLimit}
- Ship Points: ${fleetState.points.ships}
- Squadron Points: ${fleetState.points.squadrons}/${fleetState.restrictions?.squadronPointsLimit || 'N/A'}
- Ships: ${fleetState.ships.length}
- Squadrons: ${fleetState.squadrons.length}`;

    if (fleetState.restrictions) {
      restrictionsInfo = `

## Gamemode Restrictions (MUST FOLLOW)
- Max Total Points: ${fleetState.pointsLimit}
- Max Squadron Points: ${fleetState.restrictions.squadronPointsLimit}
- Max Flotillas: ${fleetState.restrictions.flotillaLimit}
- Max Aces: ${fleetState.restrictions.aceLimit}
- Commander Required: ${fleetState.restrictions.requireCommander ? 'YES - Fleet MUST have exactly 1 commander' : 'No'}
- Objectives Required: ${fleetState.restrictions.requireObjectives ? 'YES' : 'No'}`;
    }

    if (fleetState.status) {
      const violationText = fleetState.status.violations.length > 0
        ? `\n- VIOLATIONS: ${fleetState.status.violations.join(', ')}`
        : '\n- No violations (fleet is legal)';
      statusInfo = `

## Current Fleet Status
- Aces: ${fleetState.status.aceCount}/${fleetState.restrictions?.aceLimit || '?'}
- Flotillas: ${fleetState.status.flotillaCount}/${fleetState.restrictions?.flotillaLimit || '?'}
- Commanders: ${fleetState.status.commanderCount}/1${violationText}`;
    }

    if (fleetState.fleetText) {
      fleetTextInfo = `

## Current Fleet (Text Format)
\`\`\`
${fleetState.fleetText}
\`\`\``;
    }
  } else {
    context = `
## Current Fleet Context
Not connected to Star Forge. Please ensure Star Forge is open and connected.`;
  }

  return `You are an expert Star Wars Armada fleet-building assistant working with Star Forge (star-forge.tools).
${context}${restrictionsInfo}${statusInfo}${fleetTextInfo}

## IMPORTANT: Tool Usage Guide

### Reading Data (via search_cards)
When searching for cards, the API returns JSON with this structure:
\`\`\`json
{
  "success": true,
  "results": [
    {
      "id": "admiral-sloane-commander",  // USE THIS ID for add_upgrade
      "name": "Admiral Sloane",
      "type": "upgrade",
      "upgrade_type": "commander",
      "faction": ["empire"],
      "points": 24,
      "unique": true
    }
  ]
}
\`\`\`

### Adding Ships
Use the \`id\` field from search results:
- Ship IDs look like: "imperial-ii-class-star-destroyer", "quasar-fire-i-class-cruiser-carrier"
- After adding a ship, call get_fleet_state to get the ship's instanceId

### Adding Upgrades
1. First get the ship's instanceId from get_fleet_state
2. Search for upgrades to find their IDs
3. **USE get_card_details to read the card's ability text** before deciding to add it!
4. Then use add_upgrade with that instanceId and the upgrade's id

**CRITICAL: Upgrade IDs are the SPECIFIC CARD NAME, not the slot type!**
- CORRECT: "gunnery-team", "leading-shots", "expanded-hangar-bay", "admiral-ackbar-commander"
- WRONG: "officer", "turbolaser", "weapons-team" (these are SLOT TYPES, not IDs!)

The upgrade ID comes from the search results \`id\` field.

### Reading Card Details
**ALWAYS use get_card_details before adding key upgrades like commanders!**
This returns the full card text including abilities, restrictions, and synergies.
Example: \`get_card_details(cardId="admiral-ackbar-commander")\` returns the full ability text.

### Fleet State Response
get_fleet_state returns ships with these CRITICAL fields:
\`\`\`json
{
  "ships": [
    {
      "instanceId": "ship_123_abc",  // USE THIS for add_upgrade
      "id": "imperial-ii-class-star-destroyer",
      "name": "Imperial II-class Star Destroyer",
      "points": 120,
      "upgrades": [],  // Currently equipped upgrades
      "availableSlots": ["commander", "officer", "weapons-team", "offensive-retrofit", "defensive-retrofit", "turbolaser", "ion-cannon"]
    }
  ]
}
\`\`\`
**IMPORTANT**: The \`availableSlots\` array shows what upgrade types can still be added to each ship. You MUST check this before adding upgrades!

## FLEET BUILDING PHILOSOPHY: COMMANDER-FIRST APPROACH

**The commander is the heart of every fleet.** Before adding any ships, choose a commander and understand their abilities. Then build your entire fleet to maximize their strengths.

### Step 1: CHOOSE YOUR COMMANDER FIRST (MOST IMPORTANT!)
1. Search for commanders: \`search_cards(type="upgrade", query="commander", faction="empire", limit=20)\`
2. **READ THE COMMANDER'S ABILITY**: \`get_card_details(cardId="admiral-sloane-commander")\`
3. Understand what the commander wants:
   - Does it boost specific attacks? (Pick ships with matching armaments)
   - Does it support squadrons? (Build squadron-heavy)
   - Does it reward aggressive play? (Choose durable combat ships)
   - Does it need token manipulation? (Include support ships)

### Step 2: Choose a Flagship That Fits Your Commander
- Pick a ship that maximizes your commander's ability
- Example: Admiral Sloane wants lots of blue dice? Use a Quasar or ISD.
- Example: Admiral Ackbar boosts side arcs? Use MC80 or Assault Frigate.
- Add the ship: \`add_ship(shipId="imperial-ii-class-star-destroyer")\`
- Get fleet state to get instanceId: \`get_fleet_state()\`
- **IMMEDIATELY add your commander**: \`add_upgrade(shipInstanceId="...", upgradeId="admiral-sloane-commander")\`

### Step 3: Use Suggestion Tools for Smart Upgrades
After adding a ship, use the suggestion tools to see what works well on it:
- \`get_upgrade_suggestions(shipModelId="imperial-ii-class-star-destroyer")\` - Shows popular upgrades by slot
- \`get_loadout_suggestions(shipModelId="imperial-ii-class-star-destroyer")\` - Shows complete proven builds

These tools show what competitive players actually use on each ship!

### Step 4: Fill Upgrade Slots Strategically
For EACH ship, add upgrades that synergize with your commander:
\`\`\`
// Read upgrade abilities to choose ones that synergize:
get_card_details(cardId="gunnery-team")
add_upgrade(shipInstanceId="ship_123_abc", upgradeId="gunnery-team")
\`\`\`
- Weapons upgrades (turbolasers, ion-cannons) are NEUTRAL - search without faction
- Officers, titles, and unique upgrades are faction-specific
- **YOU MUST add upgrades** - bare ships are inefficient!

### Step 5: Add Support Ships
- Add additional ships that complement your strategy
- Use get_upgrade_suggestions to see popular loadouts
- Consider flotillas for activation padding and support

### Step 6: Add Squadrons That Fit Your Strategy
- If your commander supports squadrons, invest heavily
- If not, consider minimal squadrons or none
- Watch the squadron point limit and ace limit

### Step 7: Set Objectives
- Choose objectives that favor your fleet style
- Aggressive fleets want assault objectives
- Defensive fleets want navigation objectives

### Step 8: Verify Completion
- Call get_fleet_state to check for violations
- Fleet MUST have exactly 1 commander upgrade!
- Ensure points are within limits

## Upgrade Types (for searching)
When searching for upgrades, use these types:
- commander, officer, weapons-team, support-team, fleet-command
- turbolaser, ion-cannon, ordnance
- offensive-retrofit, defensive-retrofit
- title, experimental-retrofit, super-weapon

**IMPORTANT**: Most weapon upgrades (turbolasers, ion-cannons, ordnance) are NEUTRAL - they work for any faction!
- To find them, search WITHOUT faction filter: \`search_cards(query="turbolaser", limit=20)\`
- Faction-specific upgrades (commanders, some officers, titles) DO need the faction filter
- When in doubt, try searching without faction first to find neutral upgrades

## Key Rules
1. **COMMANDER FIRST** - Always choose and understand your commander before building!
2. ALWAYS call get_fleet_state first to understand what's in the fleet
3. **Use suggestion tools** - get_upgrade_suggestions and get_loadout_suggestions show proven builds
4. **ALWAYS add upgrades to your ships** - bare ships are inefficient! Fill available slots
5. Check the violations list - fix any issues before finishing
6. NEVER exceed the point limits (total, squadron, aces, flotillas)
7. Squadron points are limited to 1/3 of the total points
8. Read card abilities with get_card_details to understand synergies

## IMPORTANT: When to Stop Making Tool Calls
STOP making tool calls and provide a summary when:
- The fleet is complete and has no violations
- You've added the requested ships, upgrades, and squadrons
- The user's request has been fulfilled
- You encounter an error you cannot resolve

After completing the fleet, provide a text response summarizing:
- What you built and why
- Total points used
- Any remaining points or suggestions

Do NOT keep searching or adding cards indefinitely. Build efficiently and stop.

## Starting a New Fleet
If the user asks you to build a random or surprise fleet:
1. Use random_faction to pick a faction (25% chance each: empire, rebel, republic, separatist)
2. Use navigate_to_faction to take Star Forge to that faction's builder
3. Wait for fleet state to update (call get_fleet_state after navigation)
4. **COMMANDER FIRST**: Search for commanders, read their abilities with get_card_details
5. Choose a commander that inspires an interesting strategy
6. Add a flagship and immediately add the commander upgrade
7. Use get_upgrade_suggestions and get_loadout_suggestions to see proven ship builds
8. Build the rest of the fleet to support your commander's strategy

## Using Suggestion Tools
Two powerful tools help you build competitive fleets:

### get_upgrade_suggestions(shipModelId, upgradeType?)
Returns popular upgrades for a ship, grouped by slot type, based on real tournament data.
\`\`\`
get_upgrade_suggestions(shipModelId="imperial-ii-class-star-destroyer")
// Returns: { upgrades: [{ name: "Gunnery Team", id: "gunnery-team", usage: 45% }, ...] }
\`\`\`

### get_loadout_suggestions(shipModelId)
Returns complete proven loadouts (full upgrade packages) that players use together.
\`\`\`
get_loadout_suggestions(shipModelId="mc80-assault-cruiser")
// Returns: { loadouts: [{ upgrades: ["strategic-adviser", "leading-shots", ...], usage: 30% }] }
\`\`\`

**USE THESE TOOLS** when you're unsure what upgrades work well on a ship!

## Response Style
- Be concise but informative
- Include point costs when suggesting cards
- Use bullet points for lists
- If a tool call fails, explain the error and try an alternative`;
}

// ============================================================================
// Hook Implementation
// ============================================================================

let messageIdCounter = 0;

function generateMessageId(): string {
  return `chat_${Date.now()}_${++messageIdCounter}`;
}

export function useLLMChat(options: UseLLMChatOptions): UseLLMChat {
  const { apiKey, model, starForge } = options;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    console.log('[useLLMChat] sendMessage called with:', content);
    console.log('[useLLMChat] apiKey present:', !!apiKey, 'length:', apiKey?.length);
    console.log('[useLLMChat] model:', model);

    if (!apiKey) {
      console.log('[useLLMChat] No API key!');
      setError('Please enter your OpenRouter API key');
      return;
    }

    if (!content.trim()) {
      console.log('[useLLMChat] Empty content!');
      return;
    }

    console.log('[useLLMChat] Starting request...');
    setIsLoading(true);
    setError(null);

    // Add user message
    const userMessage: ChatMessage = {
      id: generateMessageId(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);

    try {
      // Build conversation history for API
      const conversationHistory: Message[] = messages.map(msg => ({
        role: msg.role as 'user' | 'assistant' | 'tool',
        content: msg.content,
        tool_calls: msg.toolCalls?.map(tc => ({
          id: tc.id,
          type: 'function' as const,
          function: {
            name: tc.name,
            arguments: JSON.stringify(tc.arguments),
          },
        })),
      }));

      // Add the new user message
      conversationHistory.push({ role: 'user', content });

      // Build system prompt with current context
      const systemPrompt = buildSystemPrompt(starForge.fleetState);

      // Prepend system message for API call
      const messagesWithSystem: Message[] = [
        { role: 'system', content: systemPrompt },
        ...conversationHistory,
      ];

      // Agentic loop - allow unlimited iterations until the model stops making tool calls
      let continueLoop = true;
      let loopCount = 0;

      while (continueLoop) {
        loopCount++;

        // Call LLM
        const response = await chatWithOpenRouter({
          model,
          messages: messagesWithSystem,
          tools: FLEET_BUILDING_TOOLS,
          apiKey,
        });

        // Check for tool calls
        if (response.toolCalls.length > 0) {
          // Add assistant message with tool calls to history
          messagesWithSystem.push(formatAssistantToolCalls(response.content, response.toolCalls));

          // Execute tool calls
          const toolResults = await executeToolCalls(response.toolCalls, starForge);

          // Add tool results to history
          for (const result of toolResults) {
            messagesWithSystem.push(formatToolResult(
              result.toolCallId,
              result.toolName,
              result.error || result.result
            ));
          }

          // Add tool execution message to UI
          const toolMessage: ChatMessage = {
            id: generateMessageId(),
            role: 'assistant',
            content: response.content || '',
            toolCalls: response.toolCalls,
            toolResults,
            timestamp: new Date(),
          };

          setMessages(prev => [...prev, toolMessage]);

          // Continue loop to get next response
        } else {
          // No tool calls - final response
          continueLoop = false;

          if (response.content) {
            const assistantMessage: ChatMessage = {
              id: generateMessageId(),
              role: 'assistant',
              content: response.content,
              timestamp: new Date(),
            };

            setMessages(prev => [...prev, assistantMessage]);
          }
        }
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);

      // Add error message
      const errorMsg: ChatMessage = {
        id: generateMessageId(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${errorMessage}`,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [apiKey, model, messages, starForge]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearHistory,
  };
}

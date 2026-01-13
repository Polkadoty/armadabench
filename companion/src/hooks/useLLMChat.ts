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
2. Then use add_upgrade with that instanceId and the upgrade's id
- Upgrade IDs look like: "admiral-sloane-commander", "expanded-hangar-bay"

### Fleet State Response
get_fleet_state returns the fleetText field which shows the current fleet in text format - use this to understand what's in the fleet.

## Workflow
1. Call get_fleet_state to see what's in the fleet and check for violations
2. Search for cards the user wants
3. Add ships first (they come with empty upgrade slots)
4. Get the new ship's instanceId from get_fleet_state
5. Add upgrades to ships using their instanceId
6. Add squadrons (watch the ace limit!)
7. Set objectives if required
8. Call get_fleet_state to verify no violations

## Key Rules
1. ALWAYS call get_fleet_state first to understand what's in the fleet
2. Check the violations list - fix any issues before finishing
3. NEVER exceed the point limits (total, squadron, aces, flotillas)
4. Squadron points are limited to 1/3 of the total points
5. EXPLAIN your reasoning when making suggestions
6. After making changes, call get_fleet_state to verify they worked

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

      // Agentic loop
      let continueLoop = true;
      let loopCount = 0;
      const maxLoops = 10; // Prevent infinite loops

      while (continueLoop && loopCount < maxLoops) {
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

      if (loopCount >= maxLoops) {
        setError('Response loop limit reached. Please try again.');
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

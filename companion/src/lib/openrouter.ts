/**
 * OpenRouter Client
 *
 * Provides multi-model LLM access via OpenRouter API.
 */

// ============================================================================
// Types
// ============================================================================

export interface Message {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string | null;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  name?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface Tool {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: {
      type: 'object';
      properties: Record<string, unknown>;
      required?: string[];
    };
  };
}

export interface LLMResponse {
  content: string | null;
  toolCalls: ParsedToolCall[];
  finishReason: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export interface ParsedToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  contextLength?: number;
  pricing?: {
    prompt: number;
    completion: number;
  };
}

// ============================================================================
// Available Models
// ============================================================================

export const AVAILABLE_MODELS: ModelInfo[] = [
  // Claude Haiku 4.5 - newest, fastest, great tool use, $1/M input
  {
    id: 'anthropic/claude-haiku-4.5',
    name: 'Claude Haiku 4.5',
    provider: 'Anthropic',
    contextLength: 200000,
  },
  // Claude 3.5 Haiku - previous gen Haiku, slightly cheaper
  {
    id: 'anthropic/claude-3.5-haiku',
    name: 'Claude 3.5 Haiku',
    provider: 'Anthropic',
    contextLength: 200000,
  },
  {
    id: 'anthropic/claude-sonnet-4',
    name: 'Claude Sonnet 4',
    provider: 'Anthropic',
    contextLength: 200000,
  },
  {
    id: 'anthropic/claude-3.5-sonnet',
    name: 'Claude 3.5 Sonnet',
    provider: 'Anthropic',
    contextLength: 200000,
  },
  {
    id: 'deepseek/deepseek-chat',
    name: 'DeepSeek V3',
    provider: 'DeepSeek',
    contextLength: 64000,
  },
  {
    id: 'openai/gpt-4o',
    name: 'GPT-4o',
    provider: 'OpenAI',
    contextLength: 128000,
  },
  {
    id: 'openai/gpt-4o-mini',
    name: 'GPT-4o Mini',
    provider: 'OpenAI',
    contextLength: 128000,
  },
  {
    id: 'google/gemini-2.0-flash-exp:free',
    name: 'Gemini 2.0 Flash (Free)',
    provider: 'Google',
    contextLength: 1000000,
  },
  {
    id: 'google/gemini-pro-1.5',
    name: 'Gemini 1.5 Pro',
    provider: 'Google',
    contextLength: 2000000,
  },
  {
    id: 'meta-llama/llama-3.3-70b-instruct',
    name: 'Llama 3.3 70B',
    provider: 'Meta',
    contextLength: 128000,
  },
];

// ============================================================================
// OpenRouter Client
// ============================================================================

const OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions';

export interface ChatOptions {
  model: string;
  messages: Message[];
  tools?: Tool[];
  temperature?: number;
  maxTokens?: number;
  apiKey: string;
}

export async function chatWithOpenRouter(options: ChatOptions): Promise<LLMResponse> {
  const {
    model,
    messages,
    tools,
    temperature = 0.7,
    maxTokens = 8192,
    apiKey,
  } = options;

  const body: Record<string, unknown> = {
    model,
    messages,
    temperature,
    max_tokens: maxTokens,
  };

  if (tools && tools.length > 0) {
    body.tools = tools;
    body.tool_choice = 'auto';
  }

  console.log('[OpenRouter] Making request to:', OPENROUTER_API_URL);
  console.log('[OpenRouter] Model:', model);
  console.log('[OpenRouter] Messages count:', messages.length);
  console.log('[OpenRouter] Tools count:', tools?.length || 0);

  const response = await fetch(OPENROUTER_API_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'HTTP-Referer': 'https://star-forge.tools',
      'X-Title': 'Star Forge AI Assistant',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  console.log('[OpenRouter] Response status:', response.status);

  if (!response.ok) {
    const error = await response.text();
    console.error('[OpenRouter] Error:', error);
    throw new Error(`OpenRouter API error: ${response.status} - ${error}`);
  }

  const data = await response.json();
  const choice = data.choices?.[0];

  if (!choice) {
    throw new Error('No response from OpenRouter');
  }

  // Parse tool calls if present
  const toolCalls: ParsedToolCall[] = [];
  if (choice.message?.tool_calls) {
    console.log('[OpenRouter] Tool calls received:', choice.message.tool_calls.length);
    for (const tc of choice.message.tool_calls) {
      console.log('[OpenRouter] Tool call:', tc.function.name, 'args:', tc.function.arguments);
      try {
        // Handle empty or truncated arguments
        let args: Record<string, unknown> = {};
        if (tc.function.arguments && tc.function.arguments.trim()) {
          try {
            args = JSON.parse(tc.function.arguments);
          } catch (parseError) {
            // Try to fix common JSON issues (truncation, etc)
            console.warn('[OpenRouter] Failed to parse arguments, using empty object:', tc.function.arguments);
            args = {};
          }
        }
        toolCalls.push({
          id: tc.id,
          name: tc.function.name,
          arguments: args,
        });
      } catch (e) {
        console.error('[OpenRouter] Failed to process tool call:', e);
      }
    }
  }

  return {
    content: choice.message?.content || null,
    toolCalls,
    finishReason: choice.finish_reason || 'stop',
    usage: {
      promptTokens: data.usage?.prompt_tokens || 0,
      completionTokens: data.usage?.completion_tokens || 0,
      totalTokens: data.usage?.total_tokens || 0,
    },
  };
}

// ============================================================================
// Format Tool Result for Messages
// ============================================================================

export function formatToolResult(
  toolCallId: string,
  toolName: string,
  result: unknown
): Message {
  return {
    role: 'tool',
    content: typeof result === 'string' ? result : JSON.stringify(result),
    tool_call_id: toolCallId,
    name: toolName,
  };
}

// ============================================================================
// Format Assistant Message with Tool Calls
// ============================================================================

export function formatAssistantToolCalls(
  content: string | null,
  toolCalls: ParsedToolCall[]
): Message {
  return {
    role: 'assistant',
    content,
    tool_calls: toolCalls.map(tc => ({
      id: tc.id,
      type: 'function' as const,
      function: {
        name: tc.name,
        arguments: JSON.stringify(tc.arguments),
      },
    })),
  };
}

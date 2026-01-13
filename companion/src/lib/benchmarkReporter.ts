/**
 * Benchmark Reporter
 *
 * Sends benchmark results to the benchmark dashboard API.
 */

import type { FleetStatePayload } from './postMessageProtocol';
import type { ChatMessage } from '@/hooks/useLLMChat';

export interface BenchmarkReportPayload {
  benchmarkUrl: string;
  runId: string;
  modelName: string;
  fleetState: FleetStatePayload | null;
  messages: ChatMessage[];
  toolCallsCount: number;
  duration: number;
  success: boolean;
  errorMessage?: string;
}

export async function reportBenchmarkResult(payload: BenchmarkReportPayload): Promise<void> {
  const {
    benchmarkUrl,
    runId,
    modelName,
    fleetState,
    messages,
    toolCallsCount,
    duration,
    success,
    errorMessage,
  } = payload;

  // Prepare the result data
  const resultData = {
    id: runId,
    model_name: modelName,
    faction: fleetState?.faction || null,
    gamemode: fleetState?.gamemode || 'Standard',
    points_used: fleetState?.points?.total || null,
    points_limit: fleetState?.pointsLimit || null,
    violations: fleetState?.status?.violations || [],
    fleet_text: fleetState?.fleetText || null,
    chat_log: messages.map((msg) => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      toolCalls: msg.toolCalls?.map((tc) => ({
        id: tc.id,
        name: tc.name,
        arguments: tc.arguments,
      })),
      toolResults: msg.toolResults?.map((tr) => ({
        toolName: tr.toolName,
        error: tr.error,
        // Don't include full result to save space
      })),
      timestamp: msg.timestamp,
    })),
    tool_calls_count: toolCallsCount,
    success,
    error_message: errorMessage || null,
    duration_ms: duration,
  };

  try {
    const response = await fetch(`${benchmarkUrl}/api/results`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(resultData),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[BenchmarkReporter] Failed to report result:', response.status, errorText);
    } else {
      console.log('[BenchmarkReporter] Result reported successfully');
    }
  } catch (error) {
    console.error('[BenchmarkReporter] Error reporting result:', error);
  }
}

/**
 * Star Forge AI Companion
 *
 * Main page component that orchestrates the chat interface,
 * Star Forge connection, and LLM integration.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import { AVAILABLE_MODELS } from '@/lib/openrouter';
import { useStarForgeConnection } from '@/hooks/useStarForgeConnection';
import { useLLMChat } from '@/hooks/useLLMChat';
import { ChatInterface } from '@/components/ChatInterface';
import { ConnectionStatus } from '@/components/ConnectionStatus';
import { SettingsPanel } from '@/components/SettingsPanel';
import { reportBenchmarkResult } from '@/lib/benchmarkReporter';

// ============================================================================
// Local Storage Keys
// ============================================================================

const STORAGE_KEYS = {
  apiKey: 'armadabench_openrouter_api_key',
  model: 'armadabench_model',
};

// Environment variable for API key (NEXT_PUBLIC_ prefix required for client-side access)
const ENV_API_KEY = process.env.NEXT_PUBLIC_OPENROUTER_API_KEY || '';

// ============================================================================
// Benchmark Context Types
// ============================================================================

interface BenchmarkContext {
  runId: string;
  benchmarkUrl: string;
  prompt: string;
  startTime: number;
}

// ============================================================================
// Client-only wrapper to prevent SSR issues
// ============================================================================

function CompanionAppInner() {
  const router = useRouter();

  // Settings state
  const [apiKey, setApiKey] = useState(ENV_API_KEY);
  const [model, setModel] = useState(AVAILABLE_MODELS[0].id);
  const [showSettings, setShowSettings] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Benchmark context (when launched from test runner)
  const [benchmarkContext, setBenchmarkContext] = useState<BenchmarkContext | null>(null);
  const hasAutoStartedRef = useRef(false);
  const hasReportedRef = useRef(false);

  // Star Forge connection
  const starForge = useStarForgeConnection();

  // LLM chat
  const chat = useLLMChat({
    apiKey,
    model,
    starForge,
  });

  // Parse URL parameters for benchmark mode
  useEffect(() => {
    if (!router.isReady) return;

    const {
      model: urlModel,
      runId,
      autoStart,
      benchmarkUrl,
      prompt,
    } = router.query;

    // Override model from URL if provided
    if (urlModel && typeof urlModel === 'string') {
      setModel(urlModel);
    }

    // Set up benchmark context if we have required params
    if (runId && benchmarkUrl && typeof runId === 'string' && typeof benchmarkUrl === 'string') {
      setBenchmarkContext({
        runId,
        benchmarkUrl,
        prompt: typeof prompt === 'string' ? prompt : 'Build me a random surprise fleet',
        startTime: Date.now(),
      });

      // Show benchmark mode indicator
      console.log('[Companion] Benchmark mode enabled:', { runId, benchmarkUrl, model: urlModel });
    }
  }, [router.isReady, router.query]);

  // Auto-start conversation when benchmark mode is enabled and connected
  useEffect(() => {
    if (
      benchmarkContext &&
      starForge.isConnected &&
      !hasAutoStartedRef.current &&
      !chat.isLoading &&
      chat.messages.length === 0
    ) {
      hasAutoStartedRef.current = true;
      console.log('[Companion] Auto-starting with prompt:', benchmarkContext.prompt);
      // Small delay to ensure everything is ready
      setTimeout(() => {
        chat.sendMessage(benchmarkContext.prompt);
      }, 500);
    }
  }, [benchmarkContext, starForge.isConnected, chat.isLoading, chat.messages.length, chat.sendMessage]);

  // Report results when conversation completes (not loading, has messages, last message is assistant without tool calls)
  useEffect(() => {
    if (!benchmarkContext || hasReportedRef.current) return;
    if (chat.isLoading) return;
    if (chat.messages.length === 0) return;

    const lastMessage = chat.messages[chat.messages.length - 1];

    // Check if the conversation is complete:
    // - Last message is from assistant
    // - Last message has no tool calls (indicates final response)
    // - We have some messages (not just the initial state)
    const isComplete =
      lastMessage.role === 'assistant' &&
      (!lastMessage.toolCalls || lastMessage.toolCalls.length === 0) &&
      chat.messages.length > 1;

    if (isComplete) {
      hasReportedRef.current = true;
      const duration = Date.now() - benchmarkContext.startTime;

      // Count tool calls across all messages
      const toolCallsCount = chat.messages.reduce((count, msg) => {
        return count + (msg.toolCalls?.length || 0);
      }, 0);

      // Get fleet state
      const fleetState = starForge.fleetState;

      console.log('[Companion] Reporting benchmark result:', {
        runId: benchmarkContext.runId,
        model,
        duration,
        toolCallsCount,
        faction: fleetState?.faction,
      });

      reportBenchmarkResult({
        benchmarkUrl: benchmarkContext.benchmarkUrl,
        runId: benchmarkContext.runId,
        modelName: model,
        fleetState,
        messages: chat.messages,
        toolCallsCount,
        duration,
        success: !chat.error && (fleetState?.status?.violations?.length === 0),
        errorMessage: chat.error || undefined,
      });
    }
  }, [benchmarkContext, chat.isLoading, chat.messages, chat.error, starForge.fleetState, model]);

  // Initialize from localStorage on client-side only
  useEffect(() => {
    const storedApiKey = localStorage.getItem(STORAGE_KEYS.apiKey);
    const storedModel = localStorage.getItem(STORAGE_KEYS.model);

    if (storedApiKey) setApiKey(storedApiKey);
    // Only use stored model if no URL override
    if (storedModel && !router.query.model) setModel(storedModel);

    // Show settings if no API key
    if (!storedApiKey && !ENV_API_KEY) {
      setShowSettings(true);
    }

    setIsInitialized(true);
  }, [router.query.model]);

  // Save settings handler
  const handleSaveSettings = useCallback((newApiKey: string, newModel: string) => {
    setApiKey(newApiKey);
    setModel(newModel);
    localStorage.setItem(STORAGE_KEYS.apiKey, newApiKey);
    localStorage.setItem(STORAGE_KEYS.model, newModel);
  }, []);

  // Detect dark mode preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = () => {
      document.documentElement.classList.toggle('dark', mediaQuery.matches);
    };

    handleChange(); // Set initial state
    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  if (!isInitialized) {
    return (
      <div className="h-screen flex items-center justify-center bg-background text-foreground">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      {/* Benchmark Mode Banner */}
      {benchmarkContext && (
        <div className="px-3 py-1.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 text-xs flex items-center justify-between">
          <span>
            Benchmark Mode: {model.split('/')[1]} ({benchmarkContext.runId.slice(0, 12)}...)
          </span>
          {hasReportedRef.current && (
            <span className="text-green-600 dark:text-green-400 font-semibold">
              Results reported
            </span>
          )}
        </div>
      )}

      {/* Connection Status Bar */}
      <ConnectionStatus
        isConnected={starForge.isConnected}
        fleetState={starForge.fleetState}
      />

      {/* Chat Interface */}
      <div className="flex-1 min-h-0">
        <ChatInterface
          messages={chat.messages}
          isLoading={chat.isLoading}
          error={chat.error}
          onSendMessage={chat.sendMessage}
          onClearHistory={chat.clearHistory}
          onOpenSettings={() => setShowSettings(true)}
        />
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <SettingsPanel
          apiKey={apiKey}
          model={model}
          onSave={handleSaveSettings}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}

// Dynamic import with SSR disabled
const CompanionApp = dynamic(() => Promise.resolve(CompanionAppInner), {
  ssr: false,
  loading: () => (
    <div className="h-screen flex items-center justify-center bg-background text-foreground">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  ),
});

// ============================================================================
// Home Page
// ============================================================================

export default function Home() {
  return <CompanionApp />;
}

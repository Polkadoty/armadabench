/**
 * Star Forge AI Companion
 *
 * Main page component that orchestrates the chat interface,
 * Star Forge connection, and LLM integration.
 */

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { AVAILABLE_MODELS } from '@/lib/openrouter';

// Dynamic imports for client-side only components
const ChatInterface = dynamic(() => import('@/components/ChatInterface').then(mod => ({ default: mod.ChatInterface })), { ssr: false });
const ConnectionStatus = dynamic(() => import('@/components/ConnectionStatus').then(mod => ({ default: mod.ConnectionStatus })), { ssr: false });
const SettingsPanel = dynamic(() => import('@/components/SettingsPanel').then(mod => ({ default: mod.SettingsPanel })), { ssr: false });

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
// Home Page Component
// ============================================================================

export default function Home() {
  // Settings state
  const [apiKey, setApiKey] = useState(ENV_API_KEY);
  const [model, setModel] = useState(AVAILABLE_MODELS[0].id);
  const [showSettings, setShowSettings] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Star Forge connection and LLM chat (loaded dynamically)
  const [starForge, setStarForge] = useState<ReturnType<typeof import('@/hooks/useStarForgeConnection').useStarForgeConnection> | null>(null);
  const [chat, setChat] = useState<ReturnType<typeof import('@/hooks/useLLMChat').useLLMChat> | null>(null);

  // Initialize on client-side only
  useEffect(() => {
    setMounted(true);

    // Load from localStorage
    const storedApiKey = localStorage.getItem(STORAGE_KEYS.apiKey);
    const storedModel = localStorage.getItem(STORAGE_KEYS.model);

    if (storedApiKey) setApiKey(storedApiKey);
    if (storedModel) setModel(storedModel);

    // Show settings if no API key
    if (!storedApiKey && !ENV_API_KEY) {
      setShowSettings(true);
    }
  }, []);

  // Save settings handler
  const handleSaveSettings = useCallback((newApiKey: string, newModel: string) => {
    setApiKey(newApiKey);
    setModel(newModel);
    localStorage.setItem(STORAGE_KEYS.apiKey, newApiKey);
    localStorage.setItem(STORAGE_KEYS.model, newModel);
  }, []);

  // Don't render until mounted (avoids hydration issues)
  if (!mounted) {
    return (
      <div className="h-screen flex items-center justify-center bg-background text-foreground">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return <CompanionApp
    apiKey={apiKey}
    model={model}
    showSettings={showSettings}
    setShowSettings={setShowSettings}
    onSaveSettings={handleSaveSettings}
  />;
}

// ============================================================================
// Companion App (Client-side only)
// ============================================================================

interface CompanionAppProps {
  apiKey: string;
  model: string;
  showSettings: boolean;
  setShowSettings: (show: boolean) => void;
  onSaveSettings: (apiKey: string, model: string) => void;
}

function CompanionApp({ apiKey, model, showSettings, setShowSettings, onSaveSettings }: CompanionAppProps) {
  // These hooks must be imported dynamically since they use browser APIs
  const { useStarForgeConnection } = require('@/hooks/useStarForgeConnection');
  const { useLLMChat } = require('@/hooks/useLLMChat');

  // Star Forge connection
  const starForge = useStarForgeConnection();

  // LLM chat
  const chat = useLLMChat({
    apiKey,
    model,
    starForge,
  });

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
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
          onSave={onSaveSettings}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
}

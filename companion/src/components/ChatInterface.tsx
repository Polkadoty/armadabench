/**
 * ChatInterface - Main chat UI component
 *
 * Displays conversation history, tool executions, and input field.
 */

import { useRef, useEffect, useState } from 'react';
import { Send, Loader2, Trash2, Settings, Wrench, CheckCircle, XCircle } from 'lucide-react';
import type { ChatMessage } from '@/hooks/useLLMChat';
import type { ToolExecutionResult } from '@/lib/toolExecutor';

// ============================================================================
// Message Bubble Component
// ============================================================================

interface MessageBubbleProps {
  message: ChatMessage;
}

function ToolExecutionDisplay({ results }: { results: ToolExecutionResult[] }) {
  return (
    <div className="mt-2 space-y-1">
      {results.map((result, index) => (
        <div
          key={index}
          className="flex items-center gap-2 text-xs bg-muted/50 rounded px-2 py-1"
        >
          <Wrench className="h-3 w-3 text-muted-foreground" />
          <span className="font-mono">{result.toolName}</span>
          {result.error ? (
            <XCircle className="h-3 w-3 text-red-500 ml-auto" />
          ) : (
            <CheckCircle className="h-3 w-3 text-green-500 ml-auto" />
          )}
        </div>
      ))}
    </div>
  );
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="text-center text-xs text-muted-foreground py-2">
        {message.content}
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 ${
          isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        {message.toolResults && message.toolResults.length > 0 && (
          <ToolExecutionDisplay results={message.toolResults} />
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Chat Interface Component
// ============================================================================

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  onSendMessage: (content: string) => void;
  onClearHistory: () => void;
  onOpenSettings: () => void;
}

export function ChatInterface({
  messages,
  isLoading,
  error,
  onSendMessage,
  onClearHistory,
  onOpenSettings,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b bg-background/95 backdrop-blur">
        <h1 className="text-sm font-semibold">AI Fleet Assistant</h1>
        <div className="flex items-center gap-1">
          <button
            onClick={onClearHistory}
            className="p-1.5 rounded-md hover:bg-muted transition-colors"
            title="Clear history"
          >
            <Trash2 className="h-4 w-4" />
          </button>
          <button
            onClick={onOpenSettings}
            className="p-1.5 rounded-md hover:bg-muted transition-colors"
            title="Settings"
          >
            <Settings className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground text-sm py-8">
            <p className="mb-2">Welcome to the AI Fleet Assistant!</p>
            <p className="text-xs">
              I can help you build fleets, search for cards, and answer questions about Star Wars Armada.
            </p>
          </div>
        )}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex justify-start mb-3">
            <div className="bg-muted rounded-lg px-3 py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="px-3 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-xs">
          {error}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-3 border-t bg-background/95 backdrop-blur">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about fleet building..."
            className="flex-1 min-h-[40px] max-h-[120px] px-3 py-2 text-sm rounded-md border bg-background resize-none focus:outline-none focus:ring-2 focus:ring-ring"
            rows={1}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-3 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

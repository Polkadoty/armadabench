'use client';

import { useState } from 'react';
import Link from 'next/link';

const AVAILABLE_MODELS = [
  { id: 'anthropic/claude-haiku-4.5', name: 'Claude Haiku 4.5', provider: 'Anthropic' },
  { id: 'openai/gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI' },
  { id: 'google/gemini-2.0-flash-exp:free', name: 'Gemini 2.0 Flash', provider: 'Google' },
  { id: 'deepseek/deepseek-chat', name: 'DeepSeek V3', provider: 'DeepSeek' },
  { id: 'meta-llama/llama-3.3-70b-instruct', name: 'Llama 3.3 70B', provider: 'Meta' },
  { id: 'anthropic/claude-3.5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic' },
];

const DEFAULT_PROMPT = 'Build me a random surprise fleet';

export default function Runner() {
  const [selectedModels, setSelectedModels] = useState<string[]>(['anthropic/claude-haiku-4.5']);
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [isRunning, setIsRunning] = useState(false);
  const [launchedWindows, setLaunchedWindows] = useState<{ model: string; runId: string }[]>([]);

  const generateRunId = () => `run_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  const toggleModel = (modelId: string) => {
    setSelectedModels((prev) =>
      prev.includes(modelId)
        ? prev.filter((id) => id !== modelId)
        : [...prev, modelId]
    );
  };

  const selectAllModels = () => {
    setSelectedModels(AVAILABLE_MODELS.map((m) => m.id));
  };

  const clearModels = () => {
    setSelectedModels([]);
  };

  const launchBenchmark = () => {
    if (selectedModels.length === 0) {
      alert('Please select at least one model');
      return;
    }

    setIsRunning(true);
    const benchmarkUrl = window.location.origin;
    const companionBaseUrl = 'http://localhost:5173';
    const launched: { model: string; runId: string }[] = [];

    selectedModels.forEach((modelId, index) => {
      const runId = generateRunId();
      const params = new URLSearchParams({
        model: modelId,
        runId: runId,
        autoStart: 'true',
        benchmarkUrl: benchmarkUrl,
        prompt: prompt,
      });

      const width = 420;
      const height = 700;
      const left = 50 + (index * 30); // Offset each window slightly
      const top = 50 + (index * 30);
      const features = `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`;

      const url = `${companionBaseUrl}?${params.toString()}`;
      window.open(url, `companion-${runId}`, features);

      launched.push({ model: modelId, runId });
    });

    setLaunchedWindows(launched);
  };

  return (
    <div className="min-h-screen p-8 bg-[var(--background)]">
      <header className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <Link href="/" className="text-blue-600 hover:underline">
            &larr; Back to Dashboard
          </Link>
        </div>
        <h1 className="text-3xl font-bold mb-2">Benchmark Test Runner</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Launch multiple AI agents with different models to build fleets in parallel
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Model Selection */}
        <div className="bg-gray-50 dark:bg-gray-900 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Select Models</h2>
          <div className="flex gap-2 mb-4">
            <button
              onClick={selectAllModels}
              className="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800"
            >
              Select All
            </button>
            <button
              onClick={clearModels}
              className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              Clear
            </button>
          </div>
          <div className="space-y-2">
            {AVAILABLE_MODELS.map((model) => (
              <label
                key={model.id}
                className={`flex items-center p-3 rounded cursor-pointer transition-colors ${
                  selectedModels.includes(model.id)
                    ? 'bg-blue-100 dark:bg-blue-900 border-2 border-blue-500'
                    : 'bg-white dark:bg-gray-800 border-2 border-transparent hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedModels.includes(model.id)}
                  onChange={() => toggleModel(model.id)}
                  className="mr-3"
                />
                <div>
                  <span className="font-medium">{model.name}</span>
                  <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                    ({model.provider})
                  </span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Prompt & Launch */}
        <div className="space-y-6">
          <div className="bg-gray-50 dark:bg-gray-900 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Prompt</h2>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full h-32 p-3 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 resize-none"
              placeholder="Enter the prompt for the agents..."
            />
            <button
              onClick={() => setPrompt(DEFAULT_PROMPT)}
              className="mt-2 text-sm text-blue-600 hover:underline"
            >
              Reset to default
            </button>
          </div>

          <div className="bg-gray-50 dark:bg-gray-900 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Launch</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              {selectedModels.length} model(s) selected. Each will open in its own companion window.
            </p>
            <button
              onClick={launchBenchmark}
              disabled={selectedModels.length === 0}
              className={`w-full py-3 rounded font-semibold transition-colors ${
                selectedModels.length === 0
                  ? 'bg-gray-300 dark:bg-gray-700 cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              Launch Benchmark ({selectedModels.length} agents)
            </button>
          </div>

          {launchedWindows.length > 0 && (
            <div className="bg-yellow-50 dark:bg-yellow-900/30 p-6 rounded-lg border border-yellow-200 dark:border-yellow-800">
              <h2 className="text-xl font-semibold mb-4">Running</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Benchmark launched! Results will appear on the dashboard as agents complete.
              </p>
              <ul className="space-y-2">
                {launchedWindows.map(({ model, runId }) => (
                  <li key={runId} className="text-sm font-mono">
                    <span className="text-green-600">●</span> {model.split('/')[1]} ({runId.slice(0, 15)}...)
                  </li>
                ))}
              </ul>
              <Link
                href="/"
                className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                View Dashboard
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-8 bg-gray-50 dark:bg-gray-900 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">How it works</h2>
        <ol className="list-decimal list-inside space-y-2 text-gray-700 dark:text-gray-300">
          <li>Select one or more LLM models to test</li>
          <li>Customize the prompt (or use the default &quot;Build me a random surprise fleet&quot;)</li>
          <li>Click &quot;Launch Benchmark&quot; to open companion windows for each model</li>
          <li>Each agent will automatically connect to Star Forge and start building</li>
          <li>Results are reported to this dashboard when each agent completes</li>
          <li>Compare fleet quality, build time, and tool call efficiency across models</li>
        </ol>
        <div className="mt-4 p-4 bg-yellow-100 dark:bg-yellow-900/30 rounded">
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            <strong>Note:</strong> Make sure Star Forge (localhost:3000) and the Companion app (localhost:5173) are running before launching.
          </p>
        </div>
      </div>
    </div>
  );
}

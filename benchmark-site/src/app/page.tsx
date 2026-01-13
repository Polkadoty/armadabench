'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface BenchmarkRun {
  id: string;
  model_name: string;
  faction: string | null;
  gamemode: string;
  points_used: number | null;
  points_limit: number | null;
  violations: string | null;
  fleet_text: string | null;
  chat_log: string | null;
  tool_calls_count: number | null;
  success: number;
  error_message: string | null;
  duration_ms: number | null;
  created_at: string;
}

export default function Dashboard() {
  const [runs, setRuns] = useState<BenchmarkRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const fetchRuns = async () => {
    try {
      const response = await fetch('/api/results');
      const data = await response.json();
      if (data.success) {
        setRuns(data.runs);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch results');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
    // Poll every 5 seconds for new results
    const interval = setInterval(fetchRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  const clearResults = async () => {
    if (!confirm('Are you sure you want to clear all results?')) return;
    try {
      await fetch('/api/results', { method: 'DELETE' });
      setRuns([]);
    } catch (err) {
      setError('Failed to clear results');
    }
  };

  const formatDuration = (ms: number | null) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const parseViolations = (violations: string | null): string[] => {
    if (!violations) return [];
    try {
      return JSON.parse(violations);
    } catch {
      return [];
    }
  };

  const getModelShortName = (model: string) => {
    const parts = model.split('/');
    return parts[parts.length - 1];
  };

  return (
    <div className="min-h-screen p-8 bg-[var(--background)]">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Armada Benchmark Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Track LLM fleet-building performance across different models
        </p>
      </header>

      <div className="flex gap-4 mb-6">
        <Link
          href="/runner"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Launch Test Runner
        </Link>
        <button
          onClick={fetchRuns}
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
        >
          Refresh
        </button>
        <button
          onClick={clearResults}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Clear All
        </button>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : error ? (
        <div className="text-red-500 py-8">{error}</div>
      ) : runs.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No benchmark results yet. Use the Test Runner to start a benchmark.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100 dark:bg-gray-800">
                <th className="p-3 text-left border border-gray-200 dark:border-gray-700">Model</th>
                <th className="p-3 text-left border border-gray-200 dark:border-gray-700">Faction</th>
                <th className="p-3 text-left border border-gray-200 dark:border-gray-700">Points</th>
                <th className="p-3 text-left border border-gray-200 dark:border-gray-700">Violations</th>
                <th className="p-3 text-left border border-gray-200 dark:border-gray-700">Tool Calls</th>
                <th className="p-3 text-left border border-gray-200 dark:border-gray-700">Duration</th>
                <th className="p-3 text-left border border-gray-200 dark:border-gray-700">Status</th>
                <th className="p-3 text-left border border-gray-200 dark:border-gray-700">Time</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => {
                const violations = parseViolations(run.violations);
                const isExpanded = expandedRow === run.id;

                return (
                  <>
                    <tr
                      key={run.id}
                      className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                      onClick={() => setExpandedRow(isExpanded ? null : run.id)}
                    >
                      <td className="p-3 border border-gray-200 dark:border-gray-700 font-mono text-sm">
                        {getModelShortName(run.model_name)}
                      </td>
                      <td className="p-3 border border-gray-200 dark:border-gray-700 capitalize">
                        {run.faction || '-'}
                      </td>
                      <td className="p-3 border border-gray-200 dark:border-gray-700">
                        {run.points_used !== null ? `${run.points_used}/${run.points_limit}` : '-'}
                      </td>
                      <td className="p-3 border border-gray-200 dark:border-gray-700">
                        {violations.length === 0 ? (
                          <span className="text-green-600">None</span>
                        ) : (
                          <span className="text-red-600">{violations.length}</span>
                        )}
                      </td>
                      <td className="p-3 border border-gray-200 dark:border-gray-700">
                        {run.tool_calls_count ?? '-'}
                      </td>
                      <td className="p-3 border border-gray-200 dark:border-gray-700">
                        {formatDuration(run.duration_ms)}
                      </td>
                      <td className="p-3 border border-gray-200 dark:border-gray-700">
                        {run.success ? (
                          <span className="text-green-600 font-semibold">Success</span>
                        ) : (
                          <span className="text-red-600 font-semibold">Failed</span>
                        )}
                      </td>
                      <td className="p-3 border border-gray-200 dark:border-gray-700 text-sm">
                        {formatDate(run.created_at)}
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr key={`${run.id}-details`}>
                        <td colSpan={8} className="p-4 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <h4 className="font-semibold mb-2">Fleet</h4>
                              <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded text-xs overflow-x-auto whitespace-pre-wrap">
                                {run.fleet_text || 'No fleet data'}
                              </pre>
                            </div>
                            <div>
                              <h4 className="font-semibold mb-2">Violations</h4>
                              {violations.length > 0 ? (
                                <ul className="list-disc list-inside text-red-600">
                                  {violations.map((v, i) => (
                                    <li key={i}>{v}</li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="text-green-600">No violations</p>
                              )}
                              {run.error_message && (
                                <>
                                  <h4 className="font-semibold mt-4 mb-2">Error</h4>
                                  <p className="text-red-600">{run.error_message}</p>
                                </>
                              )}
                            </div>
                          </div>
                          {run.chat_log && (
                            <div className="mt-4">
                              <h4 className="font-semibold mb-2">Chat Log</h4>
                              <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded text-xs overflow-x-auto max-h-96 overflow-y-auto">
                                {JSON.stringify(JSON.parse(run.chat_log), null, 2)}
                              </pre>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

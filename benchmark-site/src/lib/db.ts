import { createClient } from '@libsql/client';

// For local development, use a local SQLite file
// For production, use Turso cloud URL
const isProduction = process.env.NODE_ENV === 'production';

export const db = createClient({
  url: process.env.TURSO_DATABASE_URL || 'file:./benchmark.db',
  authToken: process.env.TURSO_AUTH_TOKEN,
});

// Initialize database schema
export async function initializeDatabase() {
  await db.execute(`
    CREATE TABLE IF NOT EXISTS benchmark_runs (
      id TEXT PRIMARY KEY,
      model_name TEXT NOT NULL,
      faction TEXT,
      gamemode TEXT DEFAULT 'Standard',
      points_used INTEGER,
      points_limit INTEGER,
      violations TEXT,
      fleet_text TEXT,
      chat_log TEXT,
      tool_calls_count INTEGER,
      success INTEGER DEFAULT 0,
      error_message TEXT,
      duration_ms INTEGER,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);

  await db.execute(`
    CREATE INDEX IF NOT EXISTS idx_model ON benchmark_runs(model_name)
  `);

  await db.execute(`
    CREATE INDEX IF NOT EXISTS idx_created ON benchmark_runs(created_at)
  `);
}

// Types
export interface BenchmarkRun {
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

export interface BenchmarkRunInput {
  id: string;
  model_name: string;
  faction?: string;
  gamemode?: string;
  points_used?: number;
  points_limit?: number;
  violations?: string[];
  fleet_text?: string;
  chat_log?: unknown[];
  tool_calls_count?: number;
  success?: boolean;
  error_message?: string;
  duration_ms?: number;
}

// Insert a benchmark run
export async function insertBenchmarkRun(run: BenchmarkRunInput) {
  await db.execute({
    sql: `
      INSERT INTO benchmark_runs (
        id, model_name, faction, gamemode, points_used, points_limit,
        violations, fleet_text, chat_log, tool_calls_count, success,
        error_message, duration_ms
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `,
    args: [
      run.id,
      run.model_name,
      run.faction || null,
      run.gamemode || 'Standard',
      run.points_used || null,
      run.points_limit || null,
      run.violations ? JSON.stringify(run.violations) : null,
      run.fleet_text || null,
      run.chat_log ? JSON.stringify(run.chat_log) : null,
      run.tool_calls_count || null,
      run.success ? 1 : 0,
      run.error_message || null,
      run.duration_ms || null,
    ],
  });
}

// Get all benchmark runs
export async function getAllBenchmarkRuns(): Promise<BenchmarkRun[]> {
  const result = await db.execute(
    'SELECT * FROM benchmark_runs ORDER BY created_at DESC'
  );
  return result.rows as unknown as BenchmarkRun[];
}

// Get a single benchmark run
export async function getBenchmarkRun(id: string): Promise<BenchmarkRun | null> {
  const result = await db.execute({
    sql: 'SELECT * FROM benchmark_runs WHERE id = ?',
    args: [id],
  });
  return (result.rows[0] as unknown as BenchmarkRun) || null;
}

// Delete a benchmark run
export async function deleteBenchmarkRun(id: string) {
  await db.execute({
    sql: 'DELETE FROM benchmark_runs WHERE id = ?',
    args: [id],
  });
}

// Clear all benchmark runs
export async function clearAllBenchmarkRuns() {
  await db.execute('DELETE FROM benchmark_runs');
}

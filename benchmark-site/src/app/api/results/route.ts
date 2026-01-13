import { NextRequest, NextResponse } from 'next/server';
import {
  initializeDatabase,
  insertBenchmarkRun,
  getAllBenchmarkRuns,
  clearAllBenchmarkRuns,
  BenchmarkRunInput,
} from '@/lib/db';

// CORS headers for cross-origin requests from companion
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// Handle OPTIONS preflight requests
export async function OPTIONS() {
  return NextResponse.json({}, { headers: corsHeaders });
}

// Initialize database on first request
let dbInitialized = false;

async function ensureDbInitialized() {
  if (!dbInitialized) {
    await initializeDatabase();
    dbInitialized = true;
  }
}

// GET /api/results - List all benchmark runs
export async function GET() {
  try {
    await ensureDbInitialized();
    const runs = await getAllBenchmarkRuns();
    return NextResponse.json({ success: true, runs }, { headers: corsHeaders });
  } catch (error) {
    console.error('Error fetching results:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch results' },
      { status: 500, headers: corsHeaders }
    );
  }
}

// POST /api/results - Save a benchmark run
export async function POST(request: NextRequest) {
  try {
    await ensureDbInitialized();

    const body = await request.json();

    // Validate required fields
    if (!body.id || !body.model_name) {
      return NextResponse.json(
        { success: false, error: 'Missing required fields: id, model_name' },
        { status: 400 }
      );
    }

    const run: BenchmarkRunInput = {
      id: body.id,
      model_name: body.model_name,
      faction: body.faction,
      gamemode: body.gamemode,
      points_used: body.points_used,
      points_limit: body.points_limit,
      violations: body.violations,
      fleet_text: body.fleet_text,
      chat_log: body.chat_log,
      tool_calls_count: body.tool_calls_count,
      success: body.success,
      error_message: body.error_message,
      duration_ms: body.duration_ms,
    };

    await insertBenchmarkRun(run);

    return NextResponse.json({ success: true, id: run.id }, { headers: corsHeaders });
  } catch (error) {
    console.error('Error saving result:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to save result' },
      { status: 500, headers: corsHeaders }
    );
  }
}

// DELETE /api/results - Clear all runs (for testing)
export async function DELETE() {
  try {
    await ensureDbInitialized();
    await clearAllBenchmarkRuns();
    return NextResponse.json({ success: true }, { headers: corsHeaders });
  } catch (error) {
    console.error('Error clearing results:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to clear results' },
      { status: 500, headers: corsHeaders }
    );
  }
}

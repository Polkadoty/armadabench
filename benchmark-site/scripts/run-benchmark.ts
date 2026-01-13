/**
 * Automated Benchmark Runner using Playwright
 *
 * This script:
 * 1. Opens Star Forge and navigates to a faction page
 * 2. Opens companion in same browser context (so BroadcastChannel works)
 * 3. Waits for the AI to build a fleet
 * 4. Results are automatically reported to the benchmark API
 *
 * Usage: npx tsx scripts/run-benchmark.ts [--models model1,model2] [--headless]
 */

import { chromium, Browser, BrowserContext, Page } from 'playwright';

// Configuration
const STAR_FORGE_URL = 'http://localhost:3000';
const COMPANION_URL = 'http://localhost:5173';
const BENCHMARK_URL = 'http://localhost:3001';
const DEFAULT_PROMPT = 'Build me a competitive 400 point fleet with this faction. Add a flagship with a commander, equip ships with upgrades (turbolasers, officers, titles, etc.), add support ships, and include some squadrons. Make sure to fill upgrade slots on your ships!';

// Available models to test
const AVAILABLE_MODELS = [
  'anthropic/claude-haiku-4.5',
  'openai/gpt-4o-mini',
  'google/gemini-2.0-flash-exp:free',
  'deepseek/deepseek-chat',
];

interface BenchmarkConfig {
  models: string[];
  prompt: string;
  headless: boolean;
  timeout: number; // Max time per model in ms
}

function parseArgs(): BenchmarkConfig {
  const args = process.argv.slice(2);
  const config: BenchmarkConfig = {
    models: [AVAILABLE_MODELS[0]], // Default to just Haiku
    prompt: DEFAULT_PROMPT,
    headless: false,
    timeout: 120000, // 2 minutes default
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--models' && args[i + 1]) {
      config.models = args[i + 1].split(',').map(m => m.trim());
      i++;
    } else if (args[i] === '--prompt' && args[i + 1]) {
      config.prompt = args[i + 1];
      i++;
    } else if (args[i] === '--headless') {
      config.headless = true;
    } else if (args[i] === '--timeout' && args[i + 1]) {
      config.timeout = parseInt(args[i + 1], 10);
      i++;
    } else if (args[i] === '--all') {
      config.models = AVAILABLE_MODELS;
    }
  }

  return config;
}

function generateRunId(): string {
  return `run_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

async function runBenchmarkForModel(
  context: BrowserContext,
  model: string,
  prompt: string,
  timeout: number
): Promise<void> {
  const runId = generateRunId();
  console.log(`\n🚀 Starting benchmark for ${model} (${runId})`);

  // Open Star Forge on a faction page (so FleetBuilder is loaded)
  // Pick a random faction for variety
  const factions = ['rebel', 'empire', 'republic', 'separatist'];
  const faction = factions[Math.floor(Math.random() * factions.length)];
  const starForgePage = await context.newPage();
  await starForgePage.goto(`${STAR_FORGE_URL}/${faction}`);
  console.log(`  ✓ Star Forge loaded on /${faction}`);

  // Wait for page to be fully loaded
  await starForgePage.waitForTimeout(2000);

  // Log console messages from Star Forge
  starForgePage.on('console', msg => {
    if (msg.text().includes('[FleetBuilder]') || msg.text().includes('[StarForge]')) {
      console.log(`  [SF] ${msg.text()}`);
    }
  });

  // Build companion URL with benchmark params
  const companionParams = new URLSearchParams({
    model,
    runId,
    autoStart: 'true',
    benchmarkUrl: BENCHMARK_URL,
    prompt,
  });

  const companionFullUrl = `${COMPANION_URL}?${companionParams.toString()}`;

  // Open companion as popup from Star Forge (establishes window.opener relationship)
  // This simulates clicking the AI Assistant button
  const [companionPage] = await Promise.all([
    context.waitForEvent('page'), // Wait for popup to open
    starForgePage.evaluate((url) => {
      const width = 420;
      const height = 700;
      const left = window.screenX + window.innerWidth - width - 20;
      const top = window.screenY + 80;
      const features = `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`;
      window.open(url, 'star-forge-companion', features);
    }, companionFullUrl),
  ]);

  // Log console messages from Companion
  companionPage.on('console', msg => {
    const text = msg.text();
    if (text.includes('[Companion]') || text.includes('[useLLMChat]') || text.includes('[BenchmarkReporter]') || text.includes('[ToolExecutor]')) {
      console.log(`  [C] ${text}`);
    }
  });

  await companionPage.waitForLoadState('domcontentloaded');
  console.log('  ✓ Companion opened as popup with benchmark params');

  // Wait for connection (check for "Connected" text)
  try {
    await companionPage.waitForSelector('text=Connected', { timeout: 10000 });
    console.log('  ✓ Companion connected to Star Forge');
  } catch {
    console.log('  ⚠ Connection status unclear, continuing...');
  }

  // Wait for the benchmark to complete
  // We detect completion by looking for "Results reported" text in the banner
  // or by waiting for the loading spinner to disappear after messages appear
  console.log('  ⏳ Waiting for fleet building to complete...');

  const startTime = Date.now();
  let completed = false;

  while (Date.now() - startTime < timeout && !completed) {
    try {
      // Check if pages are still open
      if (companionPage.isClosed() || starForgePage.isClosed()) {
        console.log('  ⚠ A page was closed unexpectedly');
        break;
      }

      // Check if results have been reported
      const reportedBanner = await companionPage.$('text=Results reported');
      if (reportedBanner) {
        completed = true;
        console.log('  ✓ Results reported to benchmark API');
        break;
      }

      // Check for errors in companion
      const errorElement = await companionPage.$('.bg-red-100, .bg-red-900');
      if (errorElement) {
        const errorText = await errorElement.textContent();
        if (errorText && errorText.length > 0) {
          console.log(`  ⚠ Error detected: ${errorText?.slice(0, 100)}`);
        }
      }

      await companionPage.waitForTimeout(2000);
    } catch (e) {
      console.log(`  ⚠ Error during wait: ${e}`);
      break;
    }
  }

  if (!completed) {
    console.log(`  ⚠ Timeout after ${timeout / 1000}s - results may be incomplete`);
  }

  const duration = Date.now() - startTime;
  console.log(`  ✓ Completed in ${(duration / 1000).toFixed(1)}s`);

  // Close pages
  await companionPage.close();
  await starForgePage.close();
}

async function main() {
  const config = parseArgs();

  console.log('═══════════════════════════════════════════════════════════');
  console.log('           ARMADA BENCHMARK RUNNER');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`Models to test: ${config.models.join(', ')}`);
  console.log(`Prompt: "${config.prompt}"`);
  console.log(`Headless: ${config.headless}`);
  console.log(`Timeout per model: ${config.timeout / 1000}s`);
  console.log('═══════════════════════════════════════════════════════════');

  // Launch browser
  const browser: Browser = await chromium.launch({
    headless: config.headless,
    slowMo: config.headless ? 0 : 50, // Slow down for visibility when not headless
  });

  try {
    // Run each model sequentially (they need separate Star Forge instances)
    for (const model of config.models) {
      // Create new context for each model (clean slate)
      const context = await browser.newContext({
        viewport: { width: 1400, height: 900 },
      });

      try {
        await runBenchmarkForModel(context, model, config.prompt, config.timeout);
      } catch (error) {
        console.error(`  ❌ Error running benchmark for ${model}:`, error);
      } finally {
        await context.close();
      }

      // Small delay between models
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    console.log('\n═══════════════════════════════════════════════════════════');
    console.log('           BENCHMARK COMPLETE');
    console.log('═══════════════════════════════════════════════════════════');
    console.log(`View results at: ${BENCHMARK_URL}`);
    console.log('═══════════════════════════════════════════════════════════\n');

  } finally {
    await browser.close();
  }
}

main().catch(console.error);

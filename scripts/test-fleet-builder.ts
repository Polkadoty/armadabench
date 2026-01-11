/**
 * Test script for the AI Companion fleet building
 *
 * This script automates testing of the LLM companion by:
 * 1. Opening Star Forge to a faction page
 * 2. Opening the companion in a separate tab
 * 3. Sending a fleet building request
 * 4. Monitoring the results
 */

import { chromium, Browser, Page } from 'playwright';

// Configuration
const STAR_FORGE_URL = 'http://localhost:3000';
const COMPANION_URL = 'http://localhost:5173';
const FACTION = 'empire';
const TEST_PROMPT = 'Build me a competitive 400 point Admiral Sloane fleet with a focus on squadrons. Include an Imperial Star Destroyer as the flagship.';

// Timeout for LLM responses (can be slow)
const LLM_TIMEOUT = 120000; // 2 minutes

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runTest(): Promise<void> {
  console.log('🚀 Starting fleet builder test...\n');

  let browser: Browser | null = null;

  try {
    // Launch browser (headed so we can see what's happening)
    browser = await chromium.launch({
      headless: false,
      slowMo: 100, // Slow down for visibility
    });

    const context = await browser.newContext({
      viewport: { width: 1400, height: 900 },
    });

    // Open Star Forge
    console.log('📡 Opening Star Forge...');
    const starForgePage = await context.newPage();
    await starForgePage.goto(`${STAR_FORGE_URL}/${FACTION}`, {
      waitUntil: 'networkidle',
    });
    console.log(`✅ Star Forge loaded: ${FACTION} faction\n`);

    // Wait for page to fully load
    await sleep(2000);

    // Open Companion in a new tab
    console.log('🤖 Opening AI Companion...');
    const companionPage = await context.newPage();
    await companionPage.goto(COMPANION_URL, {
      waitUntil: 'networkidle',
    });
    console.log('✅ Companion loaded\n');

    // Wait for connection to establish
    console.log('⏳ Waiting for connection...');
    await sleep(3000);

    // Check connection status
    const connectionStatus = await companionPage.locator('text=Connected').first();
    const isConnected = await connectionStatus.isVisible().catch(() => false);

    if (isConnected) {
      console.log('✅ Connected to Star Forge!\n');
    } else {
      console.log('⚠️  Connection status unclear, proceeding anyway...\n');
    }

    // Find and fill the message input
    console.log('📝 Sending fleet building request...');
    console.log(`   Prompt: "${TEST_PROMPT}"\n`);

    // Look for textarea or input
    const messageInput = await companionPage.locator('textarea, input[type="text"]').first();
    await messageInput.fill(TEST_PROMPT);

    // Find and click send button
    const sendButton = await companionPage.locator('button[type="submit"], button:has-text("Send")').first();
    await sendButton.click();

    console.log('⏳ Waiting for LLM response (this may take a minute)...\n');

    // Monitor for tool calls and responses
    let lastMessageCount = 0;
    const startTime = Date.now();

    while (Date.now() - startTime < LLM_TIMEOUT) {
      // Check for new messages in the chat
      const messages = await companionPage.locator('[class*="message"], [class*="Message"]').all();

      if (messages.length > lastMessageCount) {
        for (let i = lastMessageCount; i < messages.length; i++) {
          const text = await messages[i].textContent();
          if (text && text.trim()) {
            const preview = text.substring(0, 200).replace(/\n/g, ' ');
            console.log(`💬 Message: ${preview}${text.length > 200 ? '...' : ''}`);
          }
        }
        lastMessageCount = messages.length;
      }

      // Check if loading is complete
      const isLoading = await companionPage.locator('[class*="loading"], [class*="Loading"], [class*="spinner"]').isVisible().catch(() => false);

      if (!isLoading && lastMessageCount > 1) {
        // Give a moment to ensure response is complete
        await sleep(2000);
        const stillLoading = await companionPage.locator('[class*="loading"], [class*="Loading"], [class*="spinner"]').isVisible().catch(() => false);
        if (!stillLoading) {
          console.log('\n✅ Response complete!\n');
          break;
        }
      }

      await sleep(1000);
    }

    // Check the fleet in Star Forge
    console.log('📊 Checking fleet in Star Forge...');
    await starForgePage.bringToFront();
    await sleep(1000);

    // Try to find ships in the fleet
    const ships = await starForgePage.locator('[class*="SelectedShip"], [class*="ship-card"]').all();
    console.log(`   Ships in fleet: ${ships.length}`);

    // Try to find squadrons
    const squadrons = await starForgePage.locator('[class*="SelectedSquadron"], [class*="squadron"]').all();
    console.log(`   Squadrons in fleet: ${squadrons.length}`);

    // Try to get points total
    const pointsElement = await starForgePage.locator('text=/\\d+\\s*\\/\\s*\\d+/').first();
    const pointsText = await pointsElement.textContent().catch(() => 'Unknown');
    console.log(`   Points: ${pointsText}`);

    console.log('\n🎉 Test complete!');
    console.log('   Check the browser windows to see the results.');
    console.log('   Press Ctrl+C to close.\n');

    // Keep browser open for inspection
    await sleep(300000); // 5 minutes

  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Run the test
runTest().catch(console.error);

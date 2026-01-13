/**
 * Test script for Star Forge <-> Companion integration
 *
 * This script:
 * 1. Opens Star Forge
 * 2. Selects the Empire faction
 * 3. Clicks the AI Assistant button to open the companion popup
 * 4. Verifies the connection is established
 * 5. Sends a test message to build a fleet
 */

import { chromium, Browser, Page, BrowserContext } from 'playwright';

const STAR_FORGE_URL = 'http://localhost:3000';
const COMPANION_URL = 'http://localhost:5173';

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log('🚀 Starting companion integration test...\n');

  let browser: Browser | null = null;

  try {
    // Launch browser
    browser = await chromium.launch({
      headless: false,
      args: ['--window-size=1400,900']
    });

    const context: BrowserContext = await browser.newContext({
      viewport: { width: 1400, height: 900 }
    });

    // Collect console logs
    const logs: string[] = [];

    // Open Star Forge
    console.log('📡 Opening Star Forge...');
    const starForgePage: Page = await context.newPage();

    starForgePage.on('console', msg => {
      const text = `[StarForge] ${msg.type()}: ${msg.text()}`;
      logs.push(text);
      if (msg.text().includes('Processing companion message') ||
          msg.text().includes('BroadcastChannel') ||
          msg.text().includes('COMPANION')) {
        console.log(text);
      }
    });

    await starForgePage.goto(STAR_FORGE_URL);
    await starForgePage.waitForLoadState('networkidle');
    console.log('✅ Star Forge loaded\n');

    // Select Empire faction
    console.log('🏛️ Selecting Empire faction...');

    // Wait for faction buttons to be visible
    await starForgePage.waitForSelector('a[href="/empire"], button:has-text("Empire"), [data-faction="empire"]', { timeout: 10000 }).catch(() => {
      console.log('   Looking for Empire link...');
    });

    // Try different selectors for Empire
    const empireSelectors = [
      'a[href="/empire"]',
      'a:has-text("Empire")',
      'button:has-text("Empire")',
      '[data-faction="empire"]',
      'text=Galactic Empire'
    ];

    let clicked = false;
    for (const selector of empireSelectors) {
      try {
        const element = await starForgePage.$(selector);
        if (element) {
          await element.click();
          clicked = true;
          console.log(`   Clicked: ${selector}`);
          break;
        }
      } catch {
        // Try next selector
      }
    }

    if (!clicked) {
      // Try navigating directly
      console.log('   Navigating directly to /empire...');
      await starForgePage.goto(`${STAR_FORGE_URL}/empire`);
    }

    await starForgePage.waitForLoadState('networkidle');
    await sleep(2000); // Wait for fleet builder to initialize
    console.log('✅ Empire faction selected\n');

    // Look for AI Assistant button
    console.log('🤖 Looking for AI Assistant button...');

    const aiButtonSelectors = [
      'button:has-text("AI Assistant")',
      'button:has-text("AI")',
      'button:has(svg) >> text=AI',
      '[aria-label*="AI"]',
      'button >> svg >> xpath=../.. >> text=AI'
    ];

    let aiButton = null;
    for (const selector of aiButtonSelectors) {
      try {
        aiButton = await starForgePage.$(selector);
        if (aiButton) {
          console.log(`   Found button with: ${selector}`);
          break;
        }
      } catch {
        // Try next selector
      }
    }

    if (!aiButton) {
      // Look for any button with the robot icon SVG
      const buttons = await starForgePage.$$('button');
      for (const button of buttons) {
        const text = await button.textContent();
        if (text?.includes('AI') || text?.includes('Assistant')) {
          aiButton = button;
          console.log(`   Found button by text content: "${text}"`);
          break;
        }
      }
    }

    if (!aiButton) {
      console.log('❌ AI Assistant button not found!');
      console.log('   Make sure you are running in development mode (NODE_ENV=development)');

      // Take a screenshot for debugging
      await starForgePage.screenshot({ path: 'screenshots/ai-button-not-found.png' });
      console.log('   Screenshot saved to screenshots/ai-button-not-found.png');

      // List all buttons on the page for debugging
      console.log('\n   Available buttons on page:');
      const allButtons = await starForgePage.$$('button');
      for (const btn of allButtons.slice(0, 10)) {
        const text = await btn.textContent();
        console.log(`   - "${text?.trim().substring(0, 50)}"`);
      }

      throw new Error('AI Assistant button not found');
    }

    // Listen for popup
    console.log('\n🔗 Clicking AI Assistant button and waiting for popup...');

    const [popup] = await Promise.all([
      context.waitForEvent('page', { timeout: 10000 }),
      aiButton.click()
    ]);

    console.log('✅ Companion popup opened\n');

    // Set up console logging for companion
    popup.on('console', msg => {
      const text = `[Companion] ${msg.type()}: ${msg.text()}`;
      logs.push(text);
      console.log(text);
    });

    // Wait for companion to load
    await popup.waitForLoadState('networkidle');
    await sleep(2000);

    // Check connection status
    console.log('\n📊 Checking connection status...');

    // Look for connection indicator
    const connectionStatus = await popup.$('text=Connected') ||
                            await popup.$('[class*="connected"]') ||
                            await popup.$('text=Star Forge');

    if (connectionStatus) {
      console.log('✅ Connection established!\n');
    } else {
      console.log('⚠️ Connection status unclear - checking logs...\n');
    }

    // Wait for the chat interface
    const textarea = await popup.$('textarea');
    const sendButton = await popup.$('button[type="submit"]') || await popup.$('button:has-text("Send")');

    if (textarea && sendButton) {
      console.log('💬 Chat interface ready!\n');

      // Send a test message
      const testMessage = 'Build me a competitive 400 point Admiral Sloane fleet with a focus on squadrons.';
      console.log(`📝 Sending test message: "${testMessage.substring(0, 50)}..."\n`);

      await textarea.fill(testMessage);
      await sendButton.click();

      // Wait for response
      console.log('⏳ Waiting for AI response...\n');
      await sleep(5000);

      // Check for tool calls in the logs
      const toolCalls = logs.filter(l => l.includes('Tool call'));
      if (toolCalls.length > 0) {
        console.log('🔧 Tool calls detected:');
        toolCalls.forEach(t => console.log(`   ${t}`));
      }
    } else {
      console.log('⚠️ Chat interface not fully loaded');
    }

    // Keep browser open for manual inspection
    console.log('\n🎉 Test complete! Browser will stay open for 3 minutes for manual inspection.');
    console.log('   Star Forge: http://localhost:3000/empire');
    console.log('   Companion: (popup window)');

    await sleep(180000);

  } catch (error) {
    console.error('\n❌ Test failed:', error);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

main().catch(console.error);

#!/usr/bin/env node

/**
 * Screenshot Utility for Manual UI Capture
 *
 * This script uses Playwright to capture screenshots of the application
 * for documentation, debugging, or testing purposes.
 *
 * Usage:
 *   node scripts/screenshot.js
 *   node scripts/screenshot.js --url=http://localhost:5173/dashboard
 *   node scripts/screenshot.js --url=http://localhost:5173/dashboard --name=dashboard-view
 *   node scripts/screenshot.js --path=/features --name=features-page
 *   node scripts/screenshot.js --url=http://localhost:5173 --path=/login --name=login --fullPage
 */

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Parse command line arguments
const args = process.argv.slice(2);
const options = {};

args.forEach(arg => {
  if (arg.startsWith('--')) {
    const [key, value] = arg.substring(2).split('=');
    options[key] = value === undefined ? true : value;
  }
});

// Configuration
const DEFAULT_URL = 'http://localhost:5173';
const baseUrl = options.url || DEFAULT_URL;
const urlPath = options.path || '';
const fullUrl = urlPath ? `${baseUrl}${urlPath}` : baseUrl;
const screenshotName = options.name || `screenshot-${Date.now()}`;
const fullPage = options.fullPage !== undefined;
const width = parseInt(options.width || '1280', 10);
const height = parseInt(options.height || '720', 10);

// Screenshots directory
const screenshotsDir = path.join(__dirname, '..', 'screenshots');

// Ensure screenshots directory exists
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  console.log(`Created screenshots directory: ${screenshotsDir}`);
}

// Generate filename with timestamp
const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('.')[0];
const filename = `${screenshotName}-${timestamp}.png`;
const filepath = path.join(screenshotsDir, filename);

async function captureScreenshot() {
  let browser;

  try {
    console.log('Launching browser...');
    browser = await chromium.launch({ headless: true });

    console.log('Creating browser context...');
    const context = await browser.newContext({
      viewport: { width, height },
      deviceScaleFactor: 1
    });

    const page = await context.newPage();

    console.log(`Navigating to: ${fullUrl}`);
    await page.goto(fullUrl, { waitUntil: 'networkidle' });

    // Wait a bit for any animations or dynamic content
    await page.waitForTimeout(1000);

    console.log(`Capturing screenshot: ${filename}`);
    await page.screenshot({
      path: filepath,
      fullPage: fullPage
    });

    console.log(`\nScreenshot saved successfully!`);
    console.log(`Location: ${filepath}`);
    console.log(`URL: ${fullUrl}`);
    console.log(`Dimensions: ${width}x${height}${fullPage ? ' (full page)' : ''}`);

  } catch (error) {
    console.error('\nError capturing screenshot:');
    console.error(error.message);

    if (error.message.includes('net::ERR_CONNECTION_REFUSED')) {
      console.error('\nMake sure your development server is running:');
      console.error('  cd frontend && npm run dev');
    }

    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Display help if requested
if (options.help || options.h) {
  console.log(`
Screenshot Utility for Manual UI Capture

Usage:
  node scripts/screenshot.js [options]
  npm run screenshot -- [options]

Options:
  --url=<url>          Full URL to capture (default: http://localhost:5173)
  --path=<path>        Path to append to base URL (e.g., /dashboard)
  --name=<name>        Base name for screenshot file (default: screenshot-<timestamp>)
  --fullPage           Capture full page instead of viewport
  --width=<pixels>     Viewport width (default: 1280)
  --height=<pixels>    Viewport height (default: 720)
  --help, -h           Show this help message

Examples:
  # Capture homepage
  npm run screenshot

  # Capture dashboard page
  npm run screenshot -- --path=/dashboard --name=dashboard

  # Capture full page
  npm run screenshot -- --path=/features --name=features-full --fullPage

  # Capture with custom dimensions
  npm run screenshot -- --width=1920 --height=1080 --name=desktop-view

  # Capture different URL
  npm run screenshot -- --url=http://localhost:8000/docs --name=api-docs

Output:
  Screenshots are saved to: frontend/screenshots/
  Format: <name>-<timestamp>.png
  The screenshots/ directory is gitignored (not committed to repo)
`);
  process.exit(0);
}

// Run the screenshot capture
captureScreenshot();

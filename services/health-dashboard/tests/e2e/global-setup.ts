import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Global Setup: Starting E2E test environment...');
  
  // Optional: Setup test database, mock services, etc.
  // For now, we'll just verify the server is ready
  
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Wait for the dev server to be ready
    const baseURL = config.use?.baseURL || 'http://localhost:3000';
    console.log(`⏳ Waiting for ${baseURL} to be ready...`);
    
    await page.goto(baseURL, { waitUntil: 'networkidle', timeout: 60000 });
    console.log('✅ Dashboard is ready!');
  } catch (error) {
    console.error('❌ Failed to load dashboard:', error);
    throw error;
  } finally {
    await browser.close();
  }
  
  console.log('✅ Global Setup Complete');
}

export default globalSetup;


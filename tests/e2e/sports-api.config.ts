import { defineConfig, devices } from '@playwright/test';

/**
 * Sports API Test Configuration
 * 
 * Simplified config for testing Sports API endpoints
 * without requiring full Docker deployment setup
 */

export default defineConfig({
  testDir: '.',
  testMatch: 'sports-*.spec.ts',
  
  /* Run tests in files in parallel */
  fullyParallel: true,
  
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  
  /* Reporter to use. */
  reporter: [
    ['list'],
    ['html', { outputFolder: 'test-results/sports-api-html-report', open: 'never' }],
    ['json', { outputFile: 'test-results/sports-api-results.json' }]
  ],
  
  /* Shared settings for all the projects below. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: process.env.DASHBOARD_URL || 'http://localhost:3000',
    
    /* Collect trace when retrying the failed test. */
    trace: 'on-first-retry',
    
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Video on retry */
    video: 'retain-on-failure',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* No need to run development server - services are already running in Docker */
});


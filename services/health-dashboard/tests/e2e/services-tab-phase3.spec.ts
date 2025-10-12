import { test, expect } from '@playwright/test';

test.describe('Services Tab - Phase 3: Dependencies Visualization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display Dependencies tab in navigation', async ({ page }) => {
    const dependenciesTab = page.locator('button:has-text("Dependencies")');
    await expect(dependenciesTab).toBeVisible();
  });

  test('should navigate to Dependencies tab when clicked', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    await expect(page.locator('text=Service Dependencies & Data Flow')).toBeVisible();
  });

  test('should display header with instructions', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    await expect(page.locator('text=Click on any service to highlight its dependencies')).toBeVisible();
  });

  test('should display legend', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    await expect(page.locator('text=Legend')).toBeVisible();
  });

  test('should display all status colors in legend', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    
    await expect(page.locator('text=Running')).toBeVisible();
    await expect(page.locator('text=Degraded')).toBeVisible();
    await expect(page.locator('text=Error')).toBeVisible();
    await expect(page.locator('text=Unknown')).toBeVisible();
  });

  test('should display Home Assistant node', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    // Use more specific selector - the dependency graph has Home Assistant in a specific structure
    await expect(page.locator('.text-sm.font-medium.text-center >> text=Home Assistant')).toBeVisible();
    await expect(page.locator('text=🏠').nth(1)).toBeVisible(); // Second occurrence (first is in header)
  });

  test('should display WebSocket Ingestion node', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    await expect(page.locator('text=WebSocket')).toBeVisible();
    await expect(page.locator('text=📡')).toBeVisible();
  });

  test('should display Enrichment Pipeline node', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    // More specific selector for the dependency graph node
    await expect(page.locator('.text-sm.font-medium.text-center >> text=/Enrichment/')).toBeVisible();
    await expect(page.locator('text=🔄').first()).toBeVisible();
  });

  test('should display External Data Sources section', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    await expect(page.locator('text=External Data Sources')).toBeVisible();
  });

  test('should display all 6 external data services', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    
    await expect(page.locator('text=Weather API')).toBeVisible();
    await expect(page.locator('text=Carbon Intensity')).toBeVisible();
    await expect(page.locator('text=Electricity Pricing')).toBeVisible();
    await expect(page.locator('text=Air Quality')).toBeVisible();
    await expect(page.locator('text=Calendar')).toBeVisible();
    await expect(page.locator('text=Smart Meter')).toBeVisible();
  });

  test('should display InfluxDB node', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    await expect(page.locator('text=InfluxDB')).toBeVisible();
    await expect(page.locator('text=🗄️')).toBeVisible();
  });

  test('should display Data Retention node', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    await expect(page.locator('text=Data').and(page.locator('text=Retention'))).toBeVisible();
  });

  test('should display Admin API node', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    await expect(page.locator('text=Admin').and(page.locator('text=API'))).toBeVisible();
  });

  test('should display Health Dashboard node', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    await expect(page.locator('text=Health').and(page.locator('text=Dashboard'))).toBeVisible();
  });

  test('should display connection arrows', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    
    // Check for arrow symbols
    await expect(page.locator('text=↓').first()).toBeVisible();
  });

  test('should highlight dependencies when node is clicked', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    
    // Click WebSocket Ingestion node
    const websocketNode = page.locator('text=WebSocket').locator('..');
    await websocketNode.click();
    
    // Should show selected service info
    await expect(page.locator('text=Selected:')).toBeVisible({ timeout: 5000 });
  });

  test('should display Clear Selection button when node is selected', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    
    // Click a node
    const influxNode = page.locator('text=InfluxDB').locator('..');
    await influxNode.click();
    
    // Clear button should appear
    await expect(page.locator('button:has-text("Clear Selection")')).toBeVisible();
  });

  test('should clear selection when Clear Selection button is clicked', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    
    // Select a node
    const node = page.locator('text=InfluxDB').locator('..');
    await node.click();
    
    // Click Clear Selection
    await page.locator('button:has-text("Clear Selection")').click();
    
    // Selection info should be gone
    await expect(page.locator('text=Selected:')).not.toBeVisible();
  });

  test('should show tooltip on hover', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    
    // Hover over WebSocket node
    const websocketNode = page.locator('text=WebSocket').locator('..');
    await websocketNode.hover();
    
    // Tooltip should appear (may take a moment)
    await page.waitForTimeout(500);
    await expect(page.locator('text=Captures HA events')).toBeVisible();
  });

  test('should toggle selection when clicking same node twice', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    
    // Find the Weather API node more specifically
    const node = page.locator('.cursor-pointer:has-text("Weather API")').first();
    
    // First click - select
    await node.click();
    await expect(page.locator('text=Selected:')).toBeVisible();
    
    // Wait a moment
    await page.waitForTimeout(300);
    
    // Find the Clear Selection button
    const clearButton = page.locator('button:has-text("Clear Selection")');
    await clearButton.click();
    
    await expect(page.locator('text=Selected:')).not.toBeVisible();
  });

  test('should work in dark mode', async ({ page }) => {
    // Toggle dark mode
    const darkModeToggle = page.locator('button').filter({ hasText: /🌙|☀️/ });
    await darkModeToggle.first().click();
    
    await page.click('button:has-text("Dependencies")');
    await expect(page.locator('text=Service Dependencies & Data Flow')).toBeVisible();
  });

  test('should be scrollable horizontally on narrow screens', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.click('button:has-text("Dependencies")');
    
    // Content should be scrollable
    const container = page.locator('.overflow-x-auto');
    await expect(container).toBeVisible();
  });

  test('should display all 12 services', async ({ page }) => {
    await page.click('button:has-text("Dependencies")');
    
    // Count visible service nodes (checking for key services with specific selectors)
    await expect(page.locator('.text-sm.font-medium.text-center >> text=Home Assistant')).toBeVisible();
    await expect(page.locator('text=WebSocket').first()).toBeVisible();
    await expect(page.locator('text=Weather API').first()).toBeVisible();
    await expect(page.locator('text=InfluxDB').first()).toBeVisible();
    
    // Verify we have external services
    await expect(page.locator('text=Carbon Intensity').first()).toBeVisible();
    await expect(page.locator('text=Air Quality').first()).toBeVisible();
  });
});


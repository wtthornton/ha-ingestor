/**
 * E2E Test: Custom Tab Removal Verification
 * 
 * Verifies that the Custom tab has been successfully removed from the dashboard
 * and that all other tabs remain functional.
 */

import { test, expect } from '@playwright/test';

test.describe('Custom Tab Removal Verification', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('/');
    
    // Wait for the dashboard to load
    await page.waitForSelector('h1:has-text("HA Ingestor Dashboard")', { timeout: 10000 });
  });

  test('should display exactly 11 tabs (not 12)', async ({ page }) => {
    // Wait for tabs to render
    await page.waitForSelector('button:has-text("Overview")', { timeout: 5000 });
    
    // Count all tab buttons
    const tabButtons = page.locator('button').filter({ 
      hasText: /Overview|Services|Dependencies|Devices|Events|Logs|Sports|Data Sources|Analytics|Alerts|Configuration/
    });
    
    const count = await tabButtons.count();
    
    // Should have exactly 11 tabs (was 12 with Custom tab)
    expect(count).toBe(11);
  });

  test('should NOT display Custom tab', async ({ page }) => {
    // Wait for tabs to render
    await page.waitForSelector('button:has-text("Overview")', { timeout: 5000 });
    
    // Verify Custom tab does NOT exist
    const customTab = page.locator('button').filter({ 
      hasText: /🎨.*Custom|Custom/i
    });
    
    // Custom tab should not be present
    await expect(customTab).toHaveCount(0);
  });

  test('should display all expected tabs', async ({ page }) => {
    // Wait for tabs to render
    await page.waitForSelector('button:has-text("Overview")', { timeout: 5000 });
    
    // Expected tabs (11 total)
    const expectedTabs = [
      'Overview',
      'Services',
      'Dependencies',
      'Devices',
      'Events',
      'Logs',
      'Sports',
      'Data Sources',
      'Analytics',
      'Alerts',
      'Configuration'
    ];
    
    // Verify each expected tab exists
    for (const tabName of expectedTabs) {
      const tab = page.locator('button').filter({ hasText: new RegExp(tabName, 'i') }).first();
      await expect(tab).toBeVisible({ timeout: 2000 });
    }
  });

  test('should navigate to Overview tab successfully', async ({ page }) => {
    // Wait for Overview tab to be visible
    const overviewTab = page.locator('button').filter({ hasText: /Overview/i }).first();
    await expect(overviewTab).toBeVisible();
    
    // Click Overview tab
    await overviewTab.click();
    
    // Verify Overview content loads
    await expect(page.locator('text=Core System Components')).toBeVisible({ timeout: 5000 });
  });

  test('should navigate to Services tab successfully', async ({ page }) => {
    // Click Services tab
    const servicesTab = page.locator('button').filter({ hasText: /Services/i }).first();
    await servicesTab.click();
    
    // Verify Services content loads
    await expect(page.locator('text=Service Status Overview').or(page.locator('text=Core Services'))).toBeVisible({ timeout: 5000 });
  });

  test('should navigate to Devices tab successfully', async ({ page }) => {
    // Click Devices tab
    const devicesTab = page.locator('button').filter({ hasText: /Devices/i }).first();
    await devicesTab.click();
    
    // Verify Devices content loads (either "Total Devices" or "No devices found")
    await expect(
      page.locator('text=Total Devices').or(page.locator('text=No devices found'))
    ).toBeVisible({ timeout: 5000 });
  });

  test('should check localStorage for cleanup', async ({ page }) => {
    // Wait for page to load
    await page.waitForSelector('h1:has-text("HA Ingestor Dashboard")', { timeout: 10000 });
    
    // Check localStorage
    const dashboardLayout = await page.evaluate(() => {
      return localStorage.getItem('dashboard-layout');
    });
    
    const cleanupFlag = await page.evaluate(() => {
      return localStorage.getItem('dashboard-layout-cleanup-v1');
    });
    
    // Old dashboard-layout should be removed
    expect(dashboardLayout).toBeNull();
    
    // Cleanup flag should be set
    expect(cleanupFlag).toBe('true');
  });

  test('should display console message for localStorage cleanup (first load)', async ({ page }) => {
    // Clear localStorage to simulate first load
    await page.evaluate(() => {
      localStorage.removeItem('dashboard-layout-cleanup-v1');
      localStorage.setItem('dashboard-layout', JSON.stringify({ test: 'data' }));
    });
    
    // Listen for console messages
    const consoleMessages: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'log') {
        consoleMessages.push(msg.text());
      }
    });
    
    // Reload page to trigger cleanup
    await page.reload();
    
    // Wait for dashboard to load
    await page.waitForSelector('h1:has-text("HA Ingestor Dashboard")', { timeout: 10000 });
    
    // Check for cleanup console message
    const hasCleanupMessage = consoleMessages.some(msg => 
      msg.includes('Cleaned up deprecated Custom tab layout')
    );
    
    expect(hasCleanupMessage).toBe(true);
  });

  test('should have correct tab order', async ({ page }) => {
    // Wait for tabs to render
    await page.waitForSelector('button:has-text("Overview")', { timeout: 5000 });
    
    // Get all tab buttons
    const tabButtons = page.locator('button').filter({ 
      hasText: /Overview|Services|Dependencies|Devices|Events|Logs|Sports|Data|Analytics|Alerts|Configuration/
    });
    
    // Get text of all tabs
    const tabTexts = await tabButtons.allTextContents();
    
    // Verify Overview is first
    expect(tabTexts[0]).toContain('Overview');
    
    // Verify Custom is NOT in the list
    const hasCustomTab = tabTexts.some(text => text.toLowerCase().includes('custom'));
    expect(hasCustomTab).toBe(false);
  });

  test('should not have react-grid-layout in page resources', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Get all script sources
    const scriptSources = await page.evaluate(() => {
      const scripts = Array.from(document.querySelectorAll('script'));
      return scripts.map(script => script.src).filter(src => src);
    });
    
    // Check that no scripts reference react-grid-layout
    const hasGridLayout = scriptSources.some(src => 
      src.toLowerCase().includes('grid') || src.toLowerCase().includes('react-grid-layout')
    );
    
    // Should not load react-grid-layout
    expect(hasGridLayout).toBe(false);
  });

  test('should maintain responsive design without Custom tab', async ({ page }) => {
    // Test different viewport sizes
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' },
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      
      // Reload to apply viewport
      await page.reload();
      
      // Wait for dashboard to load
      await page.waitForSelector('h1:has-text("HA Ingestor Dashboard")', { timeout: 10000 });
      
      // Verify tabs are visible and clickable
      const overviewTab = page.locator('button').filter({ hasText: /Overview/i }).first();
      await expect(overviewTab).toBeVisible();
      
      // Verify no Custom tab at any viewport size
      const customTab = page.locator('button').filter({ hasText: /Custom/i });
      await expect(customTab).toHaveCount(0);
    }
  });
});


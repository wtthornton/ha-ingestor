import { test, expect } from '@playwright/test';

test.describe('Services Tab - Phase 1: Service Cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display Services tab in navigation', async ({ page }) => {
    const servicesTab = page.locator('button:has-text("Services")');
    await expect(servicesTab).toBeVisible();
  });

  test('should navigate to Services tab when clicked', async ({ page }) => {
    await page.click('button:has-text("Services")');
    await expect(page.locator('text=Service Management')).toBeVisible();
  });

  test('should display service cards grid', async ({ page }) => {
    await page.click('button:has-text("Services")');
    
    // Wait for services to load
    await page.waitForSelector('text=Core Services', { timeout: 10000 });
    
    // Wait for View Details buttons to appear (indicates cards are rendered)
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    
    // Check that service names are visible
    await expect(page.locator('text=websocket-ingestion')).toBeVisible();
  });

  test('should display Core Services section', async ({ page }) => {
    await page.click('button:has-text("Services")');
    await expect(page.locator('text=Core Services')).toBeVisible();
  });

  test('should display External Data Services section', async ({ page }) => {
    await page.click('button:has-text("Services")');
    await expect(page.locator('text=External Data Services')).toBeVisible();
  });

  test('should show service icons', async ({ page }) => {
    await page.click('button:has-text("Services")');
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    
    // Check for service icons that actually exist in the 6 services
    await expect(page.locator('text=🏠').first()).toBeVisible(); // WebSocket icon
    await expect(page.locator('text=🔄').first()).toBeVisible(); // Enrichment icon
    await expect(page.locator('text=💾').first()).toBeVisible(); // Data Retention icon
  });

  test('should display Auto-Refresh toggle', async ({ page }) => {
    await page.click('button:has-text("Services")');
    await expect(page.locator('button:has-text("Auto-Refresh")')).toBeVisible();
  });

  test('should toggle Auto-Refresh when clicked', async ({ page }) => {
    await page.click('button:has-text("Services")');
    
    const autoRefreshButton = page.locator('button:has-text("Auto-Refresh")');
    await expect(autoRefreshButton).toContainText('ON');
    
    await autoRefreshButton.click();
    await expect(autoRefreshButton).toContainText('OFF');
  });

  test('should display Refresh Now button', async ({ page }) => {
    await page.click('button:has-text("Services")');
    await expect(page.locator('button:has-text("Refresh Now")')).toBeVisible();
  });

  test('should show last updated timestamp', async ({ page }) => {
    await page.click('button:has-text("Services")');
    await expect(page.locator('text=Last updated:')).toBeVisible();
  });

  test('should display View Details buttons on service cards', async ({ page }) => {
    await page.click('button:has-text("Services")');
    await page.waitForSelector('text=Core Services');
    
    const viewDetailsButtons = page.locator('button:has-text("View Details")');
    await expect(viewDetailsButtons.first()).toBeVisible();
  });

  test('should display service status indicators', async ({ page }) => {
    await page.click('button:has-text("Services")');
    await page.waitForSelector('text=Core Services');
    
    // Look for status indicators (green, yellow, red circles or badges)
    const statusIndicators = page.locator('text=/running|stopped|error|degraded/i');
    await expect(statusIndicators.first()).toBeVisible({ timeout: 10000 });
  });

  test('should be responsive on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone size
    await page.click('button:has-text("Services")');
    
    await expect(page.locator('text=Core Services')).toBeVisible();
  });

  test('should work in dark mode', async ({ page }) => {
    // Toggle dark mode
    const darkModeToggle = page.locator('button').filter({ hasText: /🌙|☀️/ });
    await darkModeToggle.first().click();
    
    await page.click('button:has-text("Services")');
    await expect(page.locator('text=Core Services')).toBeVisible();
  });
});


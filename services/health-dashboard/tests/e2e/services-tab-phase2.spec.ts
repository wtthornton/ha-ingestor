import { test, expect } from '@playwright/test';

test.describe('Services Tab - Phase 2: Service Details Modal', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Navigate to Services tab
    await page.click('button:has-text("Services")');
    await page.waitForSelector('text=Core Services', { timeout: 10000 });
  });

  test('should open modal when View Details is clicked', async ({ page }) => {
    // Wait for services to load first
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    
    // Click first View Details button
    const viewDetailsButton = page.locator('button:has-text("View Details")').first();
    await viewDetailsButton.click();
    
    // Wait for modal to appear - check for specific tab buttons instead
    await expect(page.locator('button:has-text("📊 Overview")').first()).toBeVisible({ timeout: 5000 });
  });

  test('should display modal tabs', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    
    // Check all tabs are visible (use more specific selectors with emojis)
    await expect(page.locator('button:has-text("📊 Overview")').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('button:has-text("📝 Logs")').first()).toBeVisible();
    await expect(page.locator('button:has-text("📈 Metrics")').first()).toBeVisible();
    await expect(page.locator('button:has-text("💚 Health")').first()).toBeVisible();
  });

  test('should display service information in Overview tab', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    
    // Overview tab should be active by default - wait for content to load
    await page.waitForTimeout(1000); // Give modal time to render
    await expect(page.locator('text=Service Information')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Resource Usage')).toBeVisible();
  });

  test('should display CPU and Memory usage bars', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    
    await page.waitForTimeout(1000);
    await expect(page.locator('text=CPU').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Memory').first()).toBeVisible();
  });

  test('should switch to Logs tab when clicked', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    
    // Wait for modal tabs to appear
    await page.waitForSelector('button:has-text("📝 Logs")', { timeout: 5000 });
    
    // Click Logs tab
    await page.locator('button:has-text("📝 Logs")').first().click();
    await expect(page.locator('text=Recent Logs')).toBeVisible({ timeout: 5000 });
  });

  test('should display logs with timestamps and levels', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    await page.waitForSelector('button:has-text("📝 Logs")', { timeout: 5000 });
    await page.locator('button:has-text("📝 Logs")').first().click();
    
    // Check for log level badges
    await page.waitForTimeout(500);
    const logLevels = page.locator('text=/INFO|WARN|ERROR|DEBUG/');
    await expect(logLevels.first()).toBeVisible({ timeout: 5000 });
  });

  test('should display Copy Logs button', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    await page.waitForSelector('button:has-text("📝 Logs")', { timeout: 5000 });
    await page.locator('button:has-text("📝 Logs")').first().click();
    
    await expect(page.locator('button:has-text("Copy Logs")')).toBeVisible({ timeout: 5000 });
  });

  test('should switch to Metrics tab', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    await page.waitForSelector('button:has-text("📈 Metrics")', { timeout: 5000 });
    
    // Click Metrics tab
    await page.locator('button:has-text("📈 Metrics")').first().click();
    await expect(page.locator('text=Metrics Charts')).toBeVisible({ timeout: 5000 });
  });

  test('should display Chart.js installation notice', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    await page.waitForSelector('button:has-text("📈 Metrics")', { timeout: 5000 });
    await page.locator('button:has-text("📈 Metrics")').first().click();
    
    await expect(page.locator('text=Installation Required')).toBeVisible({ timeout: 5000 });
  });

  test('should switch to Health tab', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    await page.waitForSelector('button:has-text("💚 Health")', { timeout: 5000 });
    
    // Click Health tab
    await page.locator('button:has-text("💚 Health")').first().click();
    await expect(page.locator('text=Health Check Summary')).toBeVisible({ timeout: 5000 });
  });

  test('should display health statistics', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    await page.waitForSelector('button:has-text("💚 Health")', { timeout: 5000 });
    await page.locator('button:has-text("💚 Health")').first().click();
    
    await page.waitForTimeout(500);
    await expect(page.locator('text=Uptime').first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Total Checks').first()).toBeVisible();
    await expect(page.locator('text=Failed').first()).toBeVisible();
  });

  test('should display health timeline', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    await page.waitForSelector('button:has-text("💚 Health")', { timeout: 5000 });
    await page.locator('button:has-text("💚 Health")').first().click();
    
    await page.waitForTimeout(500);
    await expect(page.locator('text=Health Timeline')).toBeVisible({ timeout: 5000 });
  });

  test('should close modal with X button', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    
    // Wait for modal to open
    await page.waitForSelector('button:has-text("×")', { timeout: 5000 });
    
    // Click the X close button
    await page.locator('button:has-text("×")').click();
    
    // Modal should be gone
    await expect(page.locator('text=Service Information')).not.toBeVisible();
  });

  test('should close modal with Escape key', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    
    // Wait for modal to be visible
    await page.waitForSelector('button:has-text("×")', { timeout: 5000 });
    await page.waitForTimeout(500);
    
    // Press Escape
    await page.keyboard.press('Escape');
    
    // Modal should be gone
    await expect(page.locator('button:has-text("×")')).not.toBeVisible();
  });

  test('should close modal when clicking backdrop', async ({ page }) => {
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    await page.locator('button:has-text("View Details")').first().click();
    await page.waitForSelector('button:has-text("×")', { timeout: 5000 });
    
    // Click outside modal (on backdrop) - click coordinates outside the modal
    await page.mouse.click(50, 50);
    
    // Modal should close
    await expect(page.locator('button:has-text("×")')).not.toBeVisible();
  });

  test('should work in dark mode', async ({ page }) => {
    // Toggle dark mode
    const darkModeToggle = page.locator('button').filter({ hasText: /🌙|☀️/ });
    await darkModeToggle.first().click();
    
    // Reload services tab
    await page.click('button:has-text("Overview")');
    await page.click('button:has-text("Services")');
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    
    await page.locator('button:has-text("View Details")').first().click();
    await page.waitForTimeout(1000);
    await expect(page.locator('text=Service Information')).toBeVisible({ timeout: 5000 });
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForSelector('button:has-text("View Details")', { timeout: 10000 });
    
    await page.locator('button:has-text("View Details")').first().click();
    await page.waitForTimeout(1000);
    await expect(page.locator('text=Service Information')).toBeVisible({ timeout: 5000 });
  });
});


import { test, expect } from '@playwright/test';
import { DashboardTestHelpers } from './utils/playwright-helpers';

test.describe('Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    await DashboardTestHelpers.mockApiResponses(page);
    await DashboardTestHelpers.mockWebSocket(page);
  });

  test('dashboard layout matches snapshot', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Full page screenshot
    await expect(page).toHaveScreenshot('dashboard-full-page.png');
    
    // Component-specific screenshots
    await expect(page.locator('[data-testid="health-cards"]')).toHaveScreenshot('health-cards.png');
    await expect(page.locator('[data-testid="metrics-chart"]')).toHaveScreenshot('metrics-chart.png');
    await expect(page.locator('[data-testid="navigation"]')).toHaveScreenshot('navigation.png');
  });

  test('mobile layout matches snapshot', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    await expect(page).toHaveScreenshot('dashboard-mobile.png');
    
    // Test mobile navigation
    await page.click('[data-testid="mobile-menu-toggle"]');
    await expect(page.locator('[data-testid="mobile-menu"]')).toHaveScreenshot('mobile-menu.png');
  });

  test('tablet layout matches snapshot', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    await expect(page).toHaveScreenshot('dashboard-tablet.png');
  });

  test('dark theme matches snapshot', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Switch to dark theme
    await page.click('[data-testid="theme-toggle"]');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    
    await expect(page).toHaveScreenshot('dashboard-dark-theme.png');
  });

  test('light theme matches snapshot', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Ensure light theme
    await page.click('[data-testid="theme-toggle"]');
    await page.click('[data-testid="theme-toggle"]');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    
    await expect(page).toHaveScreenshot('dashboard-light-theme.png');
  });

  test('error states match snapshots', async ({ page }) => {
    // Mock API error
    await page.route('**/api/health', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });
    
    await page.goto('/');
    await expect(page.locator('[data-testid="error-state"]')).toBeVisible();
    
    await expect(page).toHaveScreenshot('dashboard-error-state.png');
  });

  test('loading states match snapshots', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/health', route => {
      setTimeout(() => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            overall_status: 'healthy',
            timestamp: '2024-01-01T12:00:00Z'
          })
        });
      }, 2000);
    });
    
    await page.goto('/');
    await expect(page.locator('[data-testid="loading-state"]')).toBeVisible();
    
    await expect(page).toHaveScreenshot('dashboard-loading-state.png');
  });

  test('notification states match snapshots', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Trigger different notification types
    await page.evaluate(() => {
      // Success notification
      window.dispatchEvent(new CustomEvent('test-notification', {
        detail: {
          type: 'success',
          title: 'Success',
          message: 'Operation completed successfully'
        }
      }));
    });
    
    await expect(page.locator('[data-testid="notification-toast"]')).toBeVisible();
    await expect(page).toHaveScreenshot('notification-success.png');
    
    // Dismiss and trigger warning
    await page.click('[data-testid="notification-dismiss"]');
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('test-notification', {
        detail: {
          type: 'warning',
          title: 'Warning',
          message: 'High CPU usage detected'
        }
      }));
    });
    
    await expect(page.locator('[data-testid="notification-toast"]')).toBeVisible();
    await expect(page).toHaveScreenshot('notification-warning.png');
  });

  test('status indicators match snapshots', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test different status indicators
    await expect(page.locator('[data-testid="status-indicator-healthy"]')).toHaveScreenshot('status-healthy.png');
    await expect(page.locator('[data-testid="status-indicator-warning"]')).toHaveScreenshot('status-warning.png');
    await expect(page.locator('[data-testid="status-indicator-error"]')).toHaveScreenshot('status-error.png');
  });

  test('responsive breakpoints match snapshots', async ({ page }) => {
    const breakpoints = [
      { width: 320, height: 568, name: 'mobile-xs' },
      { width: 375, height: 667, name: 'mobile-sm' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1024, height: 768, name: 'desktop-sm' },
      { width: 1440, height: 900, name: 'desktop-md' },
      { width: 1920, height: 1080, name: 'desktop-lg' },
    ];
    
    for (const breakpoint of breakpoints) {
      await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
      await page.goto('/');
      await DashboardTestHelpers.waitForDashboardLoad(page);
      
      await expect(page).toHaveScreenshot(`dashboard-${breakpoint.name}.png`);
    }
  });

  test('export dialog matches snapshot', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Open export dialog
    await page.click('[data-testid="export-data-button"]');
    await expect(page.locator('[data-testid="export-dialog"]')).toBeVisible();
    
    await expect(page.locator('[data-testid="export-dialog"]')).toHaveScreenshot('export-dialog.png');
  });

  test('settings page matches snapshot', async ({ page }) => {
    await page.goto('/settings');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    await expect(page).toHaveScreenshot('settings-page.png');
  });

  test('monitoring page matches snapshot', async ({ page }) => {
    await page.goto('/monitoring');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    await expect(page).toHaveScreenshot('monitoring-page.png');
  });
});

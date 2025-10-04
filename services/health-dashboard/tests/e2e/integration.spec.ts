import { test, expect } from '@playwright/test';
import { DashboardTestHelpers } from './utils/playwright-helpers';

test.describe('Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    await DashboardTestHelpers.mockApiResponses(page);
    await DashboardTestHelpers.mockWebSocket(page);
  });

  test('complete user workflow - dashboard to monitoring', async ({ page }) => {
    // Start at dashboard
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Verify dashboard elements
    await expect(page.locator('[data-testid="health-cards"]')).toBeVisible();
    await expect(page.locator('[data-testid="metrics-chart"]')).toBeVisible();
    
    // Navigate to monitoring
    await page.click('[data-testid="nav-monitoring"]');
    await expect(page).toHaveURL('/monitoring');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Verify monitoring page elements
    await expect(page.locator('[data-testid="monitoring-dashboard"]')).toBeVisible();
  });

  test('theme switching workflow', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test theme switching
    await DashboardTestHelpers.testThemeSwitch(page);
    
    // Verify theme persists across navigation
    await page.click('[data-testid="nav-settings"]');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'system');
  });

  test('notification workflow', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test notification system
    await DashboardTestHelpers.testNotifications(page);
    
    // Test notification preferences
    await page.click('[data-testid="notification-bell"]');
    await expect(page.locator('[data-testid="notification-center"]')).toBeVisible();
    
    await page.click('[data-testid="notification-preferences"]');
    await expect(page.locator('[data-testid="notification-preferences-dialog"]')).toBeVisible();
  });

  test('data export workflow', async ({ page }) => {
    await page.goto('/monitoring');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test data export
    await DashboardTestHelpers.testDataExport(page);
    
    // Verify export history
    await page.click('[data-testid="export-history-tab"]');
    await expect(page.locator('[data-testid="export-history"]')).toBeVisible();
  });

  test('mobile navigation workflow', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test mobile navigation
    await DashboardTestHelpers.testMobileNavigation(page);
    
    // Test mobile touch interactions
    await DashboardTestHelpers.testMobileTouchInteractions(page);
  });

  test('error handling workflow', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test error handling
    await DashboardTestHelpers.testErrorHandling(page);
    
    // Test recovery after error
    await DashboardTestHelpers.mockApiResponses(page);
    await page.reload();
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Verify normal operation restored
    await expect(page.locator('[data-testid="health-cards"]')).toBeVisible();
  });

  test('real-time updates workflow', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Simulate real-time updates
    await page.evaluate(() => {
      // Simulate WebSocket message
      window.dispatchEvent(new CustomEvent('websocket-message', {
        detail: {
          type: 'health_update',
          data: {
            overall_status: 'warning',
            message: 'High CPU usage detected'
          }
        }
      }));
    });
    
    // Verify update is reflected
    await expect(page.locator('[data-testid="status-warning"]')).toBeVisible();
    
    // Verify notification is shown
    await expect(page.locator('[data-testid="notification-toast"]')).toBeVisible();
  });

  test('settings configuration workflow', async ({ page }) => {
    await page.goto('/settings');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test theme configuration
    await page.click('[data-testid="theme-toggle"]');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    
    // Test notification preferences
    await page.click('[data-testid="notification-settings"]');
    await expect(page.locator('[data-testid="notification-preferences-dialog"]')).toBeVisible();
    
    // Test refresh interval setting
    await page.selectOption('[data-testid="refresh-interval"]', '10000');
    await expect(page.locator('[data-testid="refresh-interval"]')).toHaveValue('10000');
  });

  test('cross-browser compatibility', async ({ page, browserName }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test basic functionality across browsers
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
    await expect(page.locator('[data-testid="health-cards"]')).toBeVisible();
    
    // Test theme switching
    await page.click('[data-testid="theme-toggle"]');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    
    // Test navigation
    await page.click('[data-testid="nav-monitoring"]');
    await expect(page).toHaveURL('/monitoring');
    
    console.log(`Cross-browser test passed for ${browserName}`);
  });

  test('responsive design workflow', async ({ page }) => {
    const viewports = [
      { width: 320, height: 568, name: 'mobile-xs' },
      { width: 375, height: 667, name: 'mobile-sm' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1024, height: 768, name: 'desktop-sm' },
      { width: 1440, height: 900, name: 'desktop-md' },
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/');
      await DashboardTestHelpers.waitForDashboardLoad(page);
      
      // Verify core functionality at each breakpoint
      await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
      await expect(page.locator('[data-testid="health-cards"]')).toBeVisible();
      
      // Test navigation
      await page.click('[data-testid="nav-monitoring"]');
      await expect(page).toHaveURL('/monitoring');
      
      console.log(`Responsive test passed for ${viewport.name}`);
    }
  });

  test('accessibility workflow', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();
    
    // Test screen reader compatibility
    await expect(page.getByRole('heading', { name: /Health Dashboard/ })).toBeVisible();
    await expect(page.getByRole('main')).toBeVisible();
    
    // Test ARIA labels
    await expect(page.getByRole('button', { name: /Theme Toggle/ })).toHaveAttribute('aria-label');
    
    // Test focus management
    await page.click('[data-testid="export-data-button"]');
    await expect(page.locator('[data-testid="export-dialog"]')).toBeVisible();
    
    // Focus should be trapped in modal
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    const focusedElement = await page.locator(':focus');
    await expect(focusedElement).toHaveAttribute('data-testid', /export/);
  });

  test('performance workflow', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test performance metrics
    await DashboardTestHelpers.testPerformanceMetrics(page);
    
    // Test WebSocket performance
    await DashboardTestHelpers.testWebSocketPerformance(page);
    
    // Test with large dataset
    await page.goto('/monitoring');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Verify performance is maintained
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
      };
    });
    
    expect(metrics.loadTime).toBeLessThan(3000);
  });

  test('data persistence workflow', async ({ page }) => {
    await page.goto('/settings');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Change settings
    await page.selectOption('[data-testid="refresh-interval"]', '60000');
    await page.click('[data-testid="theme-toggle"]');
    
    // Navigate away and back
    await page.goto('/');
    await page.goto('/settings');
    
    // Verify settings persisted
    await expect(page.locator('[data-testid="refresh-interval"]')).toHaveValue('60000');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  });

  test('error recovery workflow', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Simulate network error
    await page.route('**/api/health', route => {
      route.abort('failed');
    });
    
    await page.reload();
    await expect(page.locator('[data-testid="error-state"]')).toBeVisible();
    
    // Restore network
    await page.unroute('**/api/health');
    await DashboardTestHelpers.mockApiResponses(page);
    
    // Test recovery
    await page.click('[data-testid="retry-button"]');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Verify normal operation
    await expect(page.locator('[data-testid="health-cards"]')).toBeVisible();
  });
});

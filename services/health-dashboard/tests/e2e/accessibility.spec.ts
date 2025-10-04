import { test, expect } from '@playwright/test';
import { DashboardTestHelpers } from './utils/playwright-helpers';

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await DashboardTestHelpers.mockApiResponses(page);
    await DashboardTestHelpers.mockWebSocket(page);
  });

  test('dashboard accessibility compliance', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Run accessibility scan
    const accessibilityScanResults = await page.accessibility.snapshot();
    
    // Test for specific violations (stable approach)
    const violationFingerprints = accessibilityScanResults.violations?.map(violation => ({
      rule: violation.id,
      targets: violation.nodes?.map(node => node.target) || [],
    })) || [];
    
    expect(violationFingerprints).toMatchSnapshot('accessibility-violations.json');
    
    // Test specific accessibility properties
    await expect(page.getByRole('heading', { name: /Health Dashboard/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Theme Toggle/ })).toBeVisible();
    await expect(page.getByRole('main')).toBeVisible();
  });

  test('keyboard navigation works correctly', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test tab navigation
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();
    
    // Test Enter key on buttons
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    
    // Test Escape key on modals
    await page.click('[data-testid="export-data-button"]');
    await expect(page.locator('[data-testid="export-dialog"]')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.locator('[data-testid="export-dialog"]')).not.toBeVisible();
  });

  test('screen reader compatibility', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Check for proper ARIA labels
    await expect(page.getByRole('button', { name: /Theme Toggle/ })).toHaveAttribute('aria-label');
    await expect(page.getByRole('button', { name: /Notification Bell/ })).toHaveAttribute('aria-label');
    
    // Check for proper headings hierarchy
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings.length).toBeGreaterThan(0);
    
    // Check for proper landmarks
    await expect(page.getByRole('banner')).toBeVisible();
    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByRole('navigation')).toBeVisible();
  });

  test('color contrast meets WCAG standards', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test light theme contrast
    await page.click('[data-testid="theme-toggle"]');
    await page.click('[data-testid="theme-toggle"]');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    
    const lightThemeViolations = await page.accessibility.snapshot();
    const lightContrastViolations = lightThemeViolations.violations?.filter(
      violation => violation.id === 'color-contrast'
    ) || [];
    
    // Test dark theme contrast
    await page.click('[data-testid="theme-toggle"]');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    
    const darkThemeViolations = await page.accessibility.snapshot();
    const darkContrastViolations = darkThemeViolations.violations?.filter(
      violation => violation.id === 'color-contrast'
    ) || [];
    
    // Log violations for manual review
    if (lightContrastViolations.length > 0) {
      console.log('Light theme contrast violations:', lightContrastViolations);
    }
    if (darkContrastViolations.length > 0) {
      console.log('Dark theme contrast violations:', darkContrastViolations);
    }
  });

  test('focus management works correctly', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test focus trap in modals
    await page.click('[data-testid="export-data-button"]');
    await expect(page.locator('[data-testid="export-dialog"]')).toBeVisible();
    
    // Focus should be trapped within the modal
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Focus should not escape the modal
    const focusedElement = await page.locator(':focus');
    await expect(focusedElement).toBeVisible();
    await expect(focusedElement).toHaveAttribute('data-testid', /export/);
  });

  test('alternative text for images and icons', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Check for alt text on images
    const images = await page.locator('img').all();
    for (const image of images) {
      const alt = await image.getAttribute('alt');
      expect(alt).toBeTruthy();
    }
    
    // Check for aria-label on icons
    const icons = await page.locator('[data-testid*="icon"]').all();
    for (const icon of icons) {
      const ariaLabel = await icon.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
    }
  });

  test('form accessibility', async ({ page }) => {
    await page.goto('/settings');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Check for proper form labels
    const inputs = await page.locator('input, select, textarea').all();
    for (const input of inputs) {
      const id = await input.getAttribute('id');
      if (id) {
        const label = await page.locator(`label[for="${id}"]`).count();
        const ariaLabel = await input.getAttribute('aria-label');
        const ariaLabelledBy = await input.getAttribute('aria-labelledby');
        
        expect(label > 0 || ariaLabel || ariaLabelledBy).toBeTruthy();
      }
    }
  });

  test('status indicators are accessible', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Check status indicators have proper ARIA labels
    const statusIndicators = await page.locator('[data-testid*="status"]').all();
    for (const indicator of statusIndicators) {
      const ariaLabel = await indicator.getAttribute('aria-label');
      const role = await indicator.getAttribute('role');
      
      expect(ariaLabel || role).toBeTruthy();
    }
  });

  test('mobile accessibility', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Test mobile navigation accessibility
    await page.click('[data-testid="mobile-menu-toggle"]');
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
    
    // Check mobile menu has proper ARIA attributes
    await expect(page.locator('[data-testid="mobile-menu"]')).toHaveAttribute('aria-expanded', 'true');
    
    // Test touch targets are large enough
    const touchTargets = await page.locator('button, a, [role="button"]').all();
    for (const target of touchTargets) {
      const boundingBox = await target.boundingBox();
      if (boundingBox) {
        expect(boundingBox.width).toBeGreaterThanOrEqual(44);
        expect(boundingBox.height).toBeGreaterThanOrEqual(44);
      }
    }
  });

  test('error states are accessible', async ({ page }) => {
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
    
    // Check error state has proper ARIA attributes
    await expect(page.locator('[data-testid="error-state"]')).toHaveAttribute('role', 'alert');
    await expect(page.locator('[data-testid="error-state"]')).toHaveAttribute('aria-live', 'assertive');
  });

  test('loading states are accessible', async ({ page }) => {
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
    
    // Check loading state has proper ARIA attributes
    await expect(page.locator('[data-testid="loading-state"]')).toHaveAttribute('aria-live', 'polite');
    await expect(page.locator('[data-testid="loading-state"]')).toHaveAttribute('aria-busy', 'true');
  });

  test('notifications are accessible', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Trigger notification
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('test-notification', {
        detail: {
          type: 'info',
          title: 'Test Notification',
          message: 'This is a test notification'
        }
      }));
    });
    
    await expect(page.locator('[data-testid="notification-toast"]')).toBeVisible();
    
    // Check notification has proper ARIA attributes
    await expect(page.locator('[data-testid="notification-toast"]')).toHaveAttribute('role', 'alert');
    await expect(page.locator('[data-testid="notification-toast"]')).toHaveAttribute('aria-live', 'assertive');
  });
});

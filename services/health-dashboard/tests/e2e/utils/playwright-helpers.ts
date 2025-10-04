import { Page, expect, Locator } from '@playwright/test';

export class DashboardTestHelpers {
  /**
   * Wait for the dashboard to fully load
   */
  static async waitForDashboardLoad(page: Page) {
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('[data-testid="dashboard"]', { timeout: 30000 });
    await page.waitForSelector('[data-testid="health-cards"]', { timeout: 10000 });
    await page.waitForSelector('[data-testid="metrics-chart"]', { timeout: 10000 });
  }

  /**
   * Take a screenshot of a specific component
   */
  static async takeComponentScreenshot(page: Page, selector: string, name: string) {
    await expect(page.locator(selector)).toHaveScreenshot(`${name}.png`);
  }

  /**
   * Test responsive layout at different viewport sizes
   */
  static async testResponsiveLayout(page: Page, viewport: { width: number; height: number }) {
    await page.setViewportSize(viewport);
    await this.waitForDashboardLoad(page);
    await expect(page).toHaveScreenshot(`dashboard-${viewport.width}x${viewport.height}.png`);
  }

  /**
   * Mock API responses for consistent test data
   */
  static async mockApiResponses(page: Page) {
    // Mock health API
    await page.route('**/api/health', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          overall_status: 'healthy',
          admin_api_status: 'running',
          ingestion_service: {
            status: 'healthy',
            websocket_connection: {
              is_connected: true,
              last_connection_time: '2024-01-01T12:00:00Z',
              connection_attempts: 5,
              last_error: null,
            },
            event_processing: {
              total_events: 1000,
              events_per_minute: 50,
              error_rate: 0.01,
            },
            weather_enrichment: {
              enabled: true,
              cache_hits: 100,
              api_calls: 10,
              last_error: null,
            },
            influxdb_storage: {
              is_connected: true,
              last_write_time: '2024-01-01T12:00:00Z',
              write_errors: 0,
            },
            timestamp: '2024-01-01T12:00:00Z',
          },
          timestamp: '2024-01-01T12:00:00Z',
        })
      });
    });

    // Mock metrics API
    await page.route('**/api/metrics', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          eventsPerSecond: 45,
          totalEvents: 125000,
          averageLatency: 12,
          uptime: 99.9,
          memoryUsage: 75,
          cpuUsage: 45,
        })
      });
    });

    // Mock events API
    await page.route('**/api/events', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '1',
            timestamp: '2024-01-01T12:00:00Z',
            entity_id: 'sensor.temperature',
            event_type: 'state_changed',
            new_state: { state: '22.5' },
            attributes: { unit_of_measurement: '°C' },
            domain: 'sensor',
            service: null,
            context: { id: '123' },
          },
          {
            id: '2',
            timestamp: '2024-01-01T12:01:00Z',
            entity_id: 'light.living_room',
            event_type: 'state_changed',
            new_state: { state: 'on' },
            attributes: { brightness: 255 },
            domain: 'light',
            service: null,
            context: { id: '124' },
          },
        ])
      });
    });
  }

  /**
   * Mock WebSocket connection and messages
   */
  static async mockWebSocket(page: Page) {
    await page.addInitScript(() => {
      const originalWebSocket = window.WebSocket;
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super(url);
          // Simulate connection opening
          setTimeout(() => {
            this.dispatchEvent(new Event('open'));
          }, 100);
        }

        send(data: string) {
          // Simulate receiving a response
          setTimeout(() => {
            this.dispatchEvent(new MessageEvent('message', {
              data: JSON.stringify({
                type: 'health_update',
                data: {
                  status: 'healthy',
                  message: 'System status updated'
                }
              })
            }));
          }, 200);
        }
      };
    });
  }

  /**
   * Test theme switching
   */
  static async testThemeSwitch(page: Page) {
    // Test light theme
    await page.click('[data-testid="theme-toggle"]');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    
    // Test dark theme
    await page.click('[data-testid="theme-toggle"]');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    
    // Test system theme
    await page.click('[data-testid="theme-toggle"]');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'system');
  }

  /**
   * Test mobile navigation
   */
  static async testMobileNavigation(page: Page) {
    await page.setViewportSize({ width: 375, height: 667 });
    await this.waitForDashboardLoad(page);
    
    // Test mobile menu toggle
    await page.click('[data-testid="mobile-menu-toggle"]');
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
    
    // Test navigation items
    await page.click('[data-testid="nav-dashboard"]');
    await expect(page).toHaveURL('/');
    
    await page.click('[data-testid="mobile-menu-toggle"]');
    await page.click('[data-testid="nav-monitoring"]');
    await expect(page).toHaveURL('/monitoring');
  }

  /**
   * Test notification system
   */
  static async testNotifications(page: Page) {
    // Trigger a notification
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('test-notification', {
        detail: {
          type: 'info',
          title: 'Test Notification',
          message: 'This is a test notification'
        }
      }));
    });
    
    // Check if notification appears
    await expect(page.locator('[data-testid="notification-toast"]')).toBeVisible();
    await expect(page.locator('text=Test Notification')).toBeVisible();
    
    // Test notification dismissal
    await page.click('[data-testid="notification-dismiss"]');
    await expect(page.locator('[data-testid="notification-toast"]')).not.toBeVisible();
  }

  /**
   * Test data export functionality
   */
  static async testDataExport(page: Page) {
    // Open export dialog
    await page.click('[data-testid="export-data-button"]');
    await expect(page.locator('[data-testid="export-dialog"]')).toBeVisible();
    
    // Select export format
    await page.selectOption('[data-testid="export-format"]', 'csv');
    
    // Set date range
    await page.fill('[data-testid="export-start-date"]', '2024-01-01');
    await page.fill('[data-testid="export-end-date"]', '2024-01-31');
    
    // Start export
    await page.click('[data-testid="export-start-button"]');
    
    // Wait for export to complete
    await expect(page.locator('[data-testid="export-progress"]')).toBeVisible();
    await expect(page.locator('text=Export completed')).toBeVisible({ timeout: 10000 });
  }

  /**
   * Test accessibility compliance
   */
  static async testAccessibility(page: Page) {
    // Run accessibility scan
    const accessibilityScanResults = await page.accessibility.snapshot();
    
    // Check for common accessibility issues
    const violations = accessibilityScanResults.violations || [];
    
    // Filter out known acceptable violations
    const criticalViolations = violations.filter(violation => 
      !['color-contrast', 'landmark-one-main'].includes(violation.id)
    );
    
    expect(criticalViolations).toHaveLength(0);
  }

  /**
   * Test performance metrics
   */
  static async testPerformanceMetrics(page: Page) {
    const startTime = Date.now();
    
    await page.goto('/');
    await this.waitForDashboardLoad(page);
    
    const loadTime = Date.now() - startTime;
    
    // Collect performance metrics
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
      };
    });
    
    // Assert performance thresholds
    expect(metrics.loadTime).toBeLessThan(3000); // 3 seconds
    expect(metrics.firstContentfulPaint).toBeLessThan(1500); // 1.5 seconds
    expect(loadTime).toBeLessThan(5000); // 5 seconds total
  }

  /**
   * Test WebSocket connection performance
   */
  static async testWebSocketPerformance(page: Page) {
    const connectionTimes: number[] = [];
    
    page.on('websocket', ws => {
      const startTime = Date.now();
      ws.on('open', () => {
        connectionTimes.push(Date.now() - startTime);
      });
    });
    
    await page.goto('/');
    await this.waitForDashboardLoad(page);
    
    expect(connectionTimes[0]).toBeLessThan(1000); // 1 second
  }

  /**
   * Test error handling
   */
  static async testErrorHandling(page: Page) {
    // Mock API error
    await page.route('**/api/health', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });
    
    await page.reload();
    
    // Check if error state is displayed
    await expect(page.locator('[data-testid="error-state"]')).toBeVisible();
    await expect(page.locator('text=Failed to load data')).toBeVisible();
    
    // Test retry functionality
    await page.click('[data-testid="retry-button"]');
    await expect(page.locator('[data-testid="loading-state"]')).toBeVisible();
  }

  /**
   * Test mobile touch interactions
   */
  static async testMobileTouchInteractions(page: Page) {
    await page.setViewportSize({ width: 375, height: 667 });
    await this.waitForDashboardLoad(page);
    
    // Test swipe gestures
    await page.touchscreen.tap(200, 300);
    await page.mouse.move(200, 300);
    await page.mouse.down();
    await page.mouse.move(100, 300);
    await page.mouse.up();
    
    // Test pull-to-refresh
    await page.touchscreen.tap(200, 100);
    await page.mouse.move(200, 100);
    await page.mouse.down();
    await page.mouse.move(200, 200);
    await page.mouse.up();
  }
}

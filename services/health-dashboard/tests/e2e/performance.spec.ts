import { test, expect } from '@playwright/test';
import { DashboardTestHelpers } from './utils/playwright-helpers';

test.describe('Performance Tests', () => {
  test.beforeEach(async ({ page }) => {
    await DashboardTestHelpers.mockApiResponses(page);
    await DashboardTestHelpers.mockWebSocket(page);
  });

  test('dashboard performance metrics', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    const loadTime = Date.now() - startTime;
    
    // Collect performance metrics
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');
      
      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        firstPaint: paint.find(entry => entry.name === 'first-paint')?.startTime || 0,
        firstContentfulPaint: paint.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,
        timeToInteractive: navigation.domInteractive - navigation.navigationStart,
        totalBlockingTime: 0, // Would need to calculate from performance observer
      };
    });
    
    // Assert performance thresholds
    expect(metrics.loadTime).toBeLessThan(3000); // 3 seconds
    expect(metrics.firstContentfulPaint).toBeLessThan(1500); // 1.5 seconds
    expect(metrics.timeToInteractive).toBeLessThan(5000); // 5 seconds
    expect(loadTime).toBeLessThan(5000); // 5 seconds total
    
    console.log('Performance Metrics:', metrics);
  });

  test('WebSocket connection performance', async ({ page }) => {
    const connectionTimes: number[] = [];
    
    page.on('websocket', ws => {
      const startTime = Date.now();
      ws.on('open', () => {
        connectionTimes.push(Date.now() - startTime);
      });
    });
    
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    expect(connectionTimes[0]).toBeLessThan(1000); // 1 second
    console.log('WebSocket connection time:', connectionTimes[0], 'ms');
  });

  test('API response times', async ({ page }) => {
    const apiResponseTimes: { [key: string]: number } = {};
    
    // Monitor API response times
    page.on('response', response => {
      const url = response.url();
      if (url.includes('/api/')) {
        const responseTime = response.timing().responseEnd - response.timing().responseStart;
        apiResponseTimes[url] = responseTime;
      }
    });
    
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Assert API response time thresholds
    Object.entries(apiResponseTimes).forEach(([url, time]) => {
      expect(time).toBeLessThan(1000); // 1 second per API call
      console.log(`API ${url}: ${time}ms`);
    });
  });

  test('memory usage under load', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Simulate high load by triggering many updates
    for (let i = 0; i < 100; i++) {
      await page.evaluate(() => {
        window.dispatchEvent(new CustomEvent('test-notification', {
          detail: {
            type: 'info',
            title: `Test ${i}`,
            message: `Test notification ${i}`
          }
        }));
      });
      await page.waitForTimeout(10);
    }
    
    // Check memory usage
    const memoryInfo = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory;
      }
      return null;
    });
    
    if (memoryInfo) {
      expect(memoryInfo.usedJSHeapSize).toBeLessThan(50 * 1024 * 1024); // 50MB
      console.log('Memory usage:', memoryInfo.usedJSHeapSize / 1024 / 1024, 'MB');
    }
  });

  test('large dataset performance', async ({ page }) => {
    // Mock large dataset
    await page.route('**/api/events', route => {
      const largeDataset = Array.from({ length: 10000 }, (_, i) => ({
        id: i.toString(),
        timestamp: new Date(Date.now() - i * 1000).toISOString(),
        entity_id: `sensor.test_${i % 100}`,
        event_type: 'state_changed',
        new_state: { state: Math.random().toString() },
        attributes: {},
        domain: 'sensor',
        service: null,
        context: { id: i.toString() },
      }));
      
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(largeDataset)
      });
    });
    
    const startTime = Date.now();
    
    await page.goto('/monitoring');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    const loadTime = Date.now() - startTime;
    
    expect(loadTime).toBeLessThan(10000); // 10 seconds for large dataset
    console.log('Large dataset load time:', loadTime, 'ms');
  });

  test('real-time update performance', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    const updateTimes: number[] = [];
    
    // Monitor update performance
    await page.evaluate(() => {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.name.includes('update')) {
            (window as any).updateTimes = (window as any).updateTimes || [];
            (window as any).updateTimes.push(entry.duration);
          }
        });
      });
      observer.observe({ entryTypes: ['measure'] });
    });
    
    // Trigger multiple updates
    for (let i = 0; i < 50; i++) {
      await page.evaluate(() => {
        window.dispatchEvent(new CustomEvent('test-notification', {
          detail: {
            type: 'info',
            title: `Update ${i}`,
            message: `Performance test update ${i}`
          }
        }));
      });
      await page.waitForTimeout(50);
    }
    
    const updateTimes = await page.evaluate(() => (window as any).updateTimes || []);
    
    if (updateTimes.length > 0) {
      const avgUpdateTime = updateTimes.reduce((a: number, b: number) => a + b, 0) / updateTimes.length;
      expect(avgUpdateTime).toBeLessThan(100); // 100ms average update time
      console.log('Average update time:', avgUpdateTime, 'ms');
    }
  });

  test('mobile performance', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    const startTime = Date.now();
    
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    const loadTime = Date.now() - startTime;
    
    // Mobile should be faster due to simpler layout
    expect(loadTime).toBeLessThan(3000); // 3 seconds on mobile
    console.log('Mobile load time:', loadTime, 'ms');
  });

  test('bundle size impact', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Check resource sizes
    const resources = await page.evaluate(() => {
      const entries = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
      return entries
        .filter(entry => entry.name.includes('localhost'))
        .map(entry => ({
          name: entry.name.split('/').pop(),
          size: entry.transferSize,
          duration: entry.duration,
        }));
    });
    
    // Assert bundle size thresholds
    const jsResources = resources.filter(r => r.name?.endsWith('.js'));
    const cssResources = resources.filter(r => r.name?.endsWith('.css'));
    
    const totalJSSize = jsResources.reduce((sum, r) => sum + (r.size || 0), 0);
    const totalCSSSize = cssResources.reduce((sum, r) => sum + (r.size || 0), 0);
    
    expect(totalJSSize).toBeLessThan(2 * 1024 * 1024); // 2MB total JS
    expect(totalCSSSize).toBeLessThan(500 * 1024); // 500KB total CSS
    
    console.log('Total JS size:', totalJSSize / 1024 / 1024, 'MB');
    console.log('Total CSS size:', totalCSSSize / 1024, 'KB');
  });

  test('lazy loading performance', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    // Navigate to different pages to test lazy loading
    const pages = ['/monitoring', '/settings'];
    
    for (const pagePath of pages) {
      const startTime = Date.now();
      await page.goto(pagePath);
      await DashboardTestHelpers.waitForDashboardLoad(page);
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(2000); // 2 seconds for lazy loaded pages
      console.log(`Page ${pagePath} load time:`, loadTime, 'ms');
    }
  });

  test('WebSocket message handling performance', async ({ page }) => {
    await page.goto('/');
    await DashboardTestHelpers.waitForDashboardLoad(page);
    
    const messageHandlingTimes: number[] = [];
    
    // Mock WebSocket with performance monitoring
    await page.addInitScript(() => {
      const originalWebSocket = window.WebSocket;
      window.WebSocket = class extends originalWebSocket {
        constructor(url: string) {
          super(url);
          setTimeout(() => {
            this.dispatchEvent(new Event('open'));
          }, 100);
        }

        addEventListener(type: string, listener: any) {
          if (type === 'message') {
            const wrappedListener = (event: MessageEvent) => {
              const startTime = performance.now();
              listener(event);
              const endTime = performance.now();
              (window as any).messageHandlingTimes = (window as any).messageHandlingTimes || [];
              (window as any).messageHandlingTimes.push(endTime - startTime);
            };
            super.addEventListener(type, wrappedListener);
          } else {
            super.addEventListener(type, listener);
          }
        }
      };
    });
    
    // Trigger WebSocket messages
    for (let i = 0; i < 100; i++) {
      await page.evaluate(() => {
        const ws = new WebSocket('ws://localhost:3000');
        ws.onopen = () => {
          ws.dispatchEvent(new MessageEvent('message', {
            data: JSON.stringify({
              type: 'health_update',
              data: { status: 'healthy', message: `Update ${i}` }
            })
          }));
        };
      });
      await page.waitForTimeout(10);
    }
    
    const messageHandlingTimes = await page.evaluate(() => (window as any).messageHandlingTimes || []);
    
    if (messageHandlingTimes.length > 0) {
      const avgHandlingTime = messageHandlingTimes.reduce((a: number, b: number) => a + b, 0) / messageHandlingTimes.length;
      expect(avgHandlingTime).toBeLessThan(50); // 50ms average handling time
      console.log('Average message handling time:', avgHandlingTime, 'ms');
    }
  });
});

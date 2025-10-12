# 🎭 Playwright Testing Plan - BMAD Framework

**Date:** October 12, 2025  
**Status:** 🔄 IN PROGRESS  
**Framework:** BMAD + Playwright Automation

---

## 🎯 Mission Statement

**Objective:** Use Playwright to systematically test, diagnose, fix, and verify the complete HA Ingestor dashboard deployment.

**Problem:** Dashboard not opening in browser - need automated diagnosis and testing.

---

## 📋 Testing Strategy

### Phase 1: Diagnosis & Discovery
- Navigate to dashboard and capture screenshots
- Analyze network requests and console errors
- Identify specific failure points
- Document current state

### Phase 2: Issue Resolution
- Fix any identified issues
- Restart services if needed
- Verify fixes with automated tests

### Phase 3: Comprehensive Testing
- Test all dashboard functionality
- Verify sports tab integration
- Test API endpoints through UI
- Validate real-time features

### Phase 4: Deployment Verification
- End-to-end user journey testing
- Performance validation
- Error handling verification
- Production readiness assessment

---

## 🧪 Test Scenarios

### 1. Dashboard Accessibility
```javascript
// Test dashboard loads and is accessible
test('Dashboard loads successfully', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await expect(page).toHaveTitle(/HA Ingestor|Dashboard/);
  await page.screenshot({ path: 'dashboard-load-test.png' });
});
```

### 2. Network Request Analysis
```javascript
// Analyze all network requests for errors
test('Network requests analysis', async ({ page }) => {
  const requests = [];
  const responses = [];
  
  page.on('request', request => requests.push(request.url()));
  page.on('response', response => {
    if (!response.ok()) {
      responses.push({ url: response.url(), status: response.status() });
    }
  });
  
  await page.goto('http://localhost:3000');
  await page.waitForTimeout(5000);
  
  // Analyze failed requests
  console.log('Failed responses:', responses);
});
```

### 3. Console Error Detection
```javascript
// Capture and analyze console errors
test('Console error detection', async ({ page }) => {
  const consoleErrors = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  
  await page.goto('http://localhost:3000');
  await page.waitForTimeout(3000);
  
  expect(consoleErrors).toHaveLength(0);
});
```

### 4. Sports Tab Functionality
```javascript
// Test sports tab specifically
test('Sports tab functionality', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Wait for dashboard to load
  await page.waitForSelector('[data-testid="sports-tab"], .sports-tab, [href*="sports"]', { timeout: 10000 });
  
  // Click sports tab
  await page.click('[data-testid="sports-tab"], .sports-tab, [href*="sports"]');
  
  // Verify sports content loads
  await page.waitForSelector('.sports-content, [data-testid="sports-content"]', { timeout: 5000 });
  
  // Check for team selection or games
  await page.screenshot({ path: 'sports-tab-test.png' });
});
```

### 5. API Endpoint Testing
```javascript
// Test API endpoints through UI
test('API endpoints through UI', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Monitor network requests
  const apiRequests = [];
  page.on('response', response => {
    if (response.url().includes('/api/')) {
      apiRequests.push({
        url: response.url(),
        status: response.status(),
        ok: response.ok()
      });
    }
  });
  
  // Navigate to sports tab to trigger API calls
  await page.click('[data-testid="sports-tab"], .sports-tab, [href*="sports"]');
  await page.waitForTimeout(3000);
  
  // Verify API calls succeeded
  const failedRequests = apiRequests.filter(req => !req.ok);
  expect(failedRequests).toHaveLength(0);
});
```

---

## 🔧 Diagnostic Tests

### Service Health Check
```javascript
// Verify all services are running
test('Service health verification', async ({ page }) => {
  // Test direct service endpoints
  const services = [
    'http://localhost:3000',      // Dashboard
    'http://localhost:8005/health', // Sports data
    'http://localhost:8003/api/v1/services', // Admin API
  ];
  
  for (const service of services) {
    const response = await page.request.get(service);
    expect(response.status()).toBeLessThan(500);
  }
});
```

### Port Accessibility
```javascript
// Test port accessibility
test('Port accessibility', async ({ page }) => {
  const ports = [3000, 8003, 8005];
  
  for (const port of ports) {
    try {
      const response = await page.request.get(`http://localhost:${port}`);
      console.log(`Port ${port}: ${response.status()}`);
    } catch (error) {
      console.error(`Port ${port} not accessible:`, error.message);
    }
  }
});
```

---

## 🚀 Execution Plan

### Step 1: Initial Diagnosis
1. Start Playwright browser
2. Navigate to dashboard
3. Capture screenshots and errors
4. Analyze network requests
5. Document findings

### Step 2: Service Verification
1. Test direct service endpoints
2. Check Docker container status
3. Verify port accessibility
4. Analyze service logs

### Step 3: Issue Resolution
1. Fix any identified issues
2. Restart services if needed
3. Update configurations
4. Re-test with Playwright

### Step 4: Comprehensive Testing
1. Run full test suite
2. Test all dashboard features
3. Verify sports integration
4. Performance testing

### Step 5: Final Verification
1. End-to-end user journey
2. Error handling validation
3. Production readiness check
4. Documentation update

---

## 📊 Expected Outcomes

### Success Criteria:
- ✅ Dashboard loads without errors
- ✅ Sports tab functional
- ✅ API endpoints responding
- ✅ No console errors
- ✅ All network requests successful
- ✅ User interactions working

### Failure Scenarios:
- ❌ Dashboard won't load
- ❌ API endpoints failing
- ❌ Console errors present
- ❌ Network requests failing
- ❌ Service connectivity issues

---

## 🛠️ Tools & Commands

### Playwright Setup:
```bash
# Install Playwright if needed
npm install -g playwright
npx playwright install

# Run specific tests
npx playwright test dashboard.spec.js
npx playwright test --headed  # Run with visible browser
npx playwright test --debug   # Debug mode
```

### Docker Commands:
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs health-dashboard
docker-compose logs sports-data

# Restart services
docker-compose restart health-dashboard
```

---

## 📁 Test Files Structure

```
tests/
├── playwright.config.js
├── dashboard.spec.js
├── sports-integration.spec.js
├── api-endpoints.spec.js
└── utils/
    ├── helpers.js
    └── fixtures.js
```

---

## 🎯 Success Metrics

### Technical Metrics:
- **Page Load Time**: < 3 seconds
- **API Response Time**: < 500ms
- **Error Rate**: 0%
- **Service Uptime**: 100%

### Functional Metrics:
- **Dashboard Accessibility**: ✅
- **Sports Tab Functionality**: ✅
- **Team Selection**: ✅
- **Real-time Updates**: ✅

---

**🚀 Ready to execute Playwright testing plan!**

*This plan will systematically diagnose, fix, and verify the complete dashboard deployment using automated testing.*

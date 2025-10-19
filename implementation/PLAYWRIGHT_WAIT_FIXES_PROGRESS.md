# Playwright Hard-Coded Wait Fixes - Progress Report

**Date:** October 19, 2025  
**Context7 KB Used:** `/microsoft/playwright` - Web-first assertions best practices  
**Status:** In Progress (8/68 fixed)

---

## Summary

**Total hard-coded `waitForTimeout` calls found:** 68  
**Files affected:** 15  
**Pattern:** Replace `await page.waitForTimeout(ms)` with web-first assertions

---

## ✅ Completed Files

### 1. `tests/e2e/dashboard-functionality.spec.ts` - 8 instances fixed

**Changes made:**
1. **Refresh controls** - Line 60: Replaced 2s wait with visibility check
   ```typescript
   // ❌ BEFORE
   await page.waitForTimeout(2000);
   
   // ✅ AFTER
   await expect(page.locator('[data-testid="health-cards"]')).toBeVisible();
   ```

2. **Layout switcher** - Lines 75, 79, 83: Replaced 3x 1s waits with layout visibility checks
   ```typescript
   // ❌ BEFORE
   await layoutSwitcher.selectOption('grid');
   await page.waitForTimeout(1000);
   
   // ✅ AFTER
   await layoutSwitcher.selectOption('grid');
   await expect(page.locator('[data-testid="grid-layout"]')).toBeVisible({ timeout: 2000 });
   ```

3. **Chart updates** - Lines 122, 125: Replaced 2x 2s waits with chart visibility checks
   ```typescript
   // ❌ BEFORE
   await timeRangeSelect.selectOption('1h');
   await page.waitForTimeout(2000);
   
   // ✅ AFTER
   await timeRangeSelect.selectOption('1h');
   await expect(chart).toBeVisible(); // Chart remains visible during update
   ```

4. **Theme toggle** - Lines 176, 184: Replaced 2x 1s waits with class checks
   ```typescript
   // ❌ BEFORE
   await themeToggle.click();
   await page.waitForTimeout(1000);
   await expect(body).toHaveClass(/dark/);
   
   // ✅ AFTER
   await themeToggle.click();
   await expect(body).toHaveClass(/dark/); // Waits automatically
   ```

---

## 📋 Remaining Files (60 instances)

### High Priority (User-Facing Tests)

1. **`tests/e2e/performance.spec.ts`** - 11 instances
   - Lines: 123, 182, 227, 229, 231, 235, 274, 276, 278, 326
   - **Pattern:** Chart updates, refresh cycles, message processing
   - **Fix:** Use `expect().toBeVisible()` or `expect().toHaveText()`

2. **`tests/e2e/visual-regression.spec.ts`** - 17 instances
   - Lines: 20, 48, 72, 86, 152, 161, 168, 174, 187, 195, 206, 214, 220, 240, 339, 347
   - **Pattern:** Animation completion waits
   - **Fix:** Wait for stable screenshot with `page.waitForLoadState('networkidle')`

3. **`tests/e2e/monitoring-screen.spec.ts`** - 4 instances
   - Lines: 74, 138, 171, 213
   - **Pattern:** Data loading waits
   - **Fix:** Use `expect().toContainText()` or `expect().toBeVisible()`

4. **`tests/e2e/integration.spec.ts`** - 3 instances
   - Lines: 96, 220, 275
   - **Pattern:** Error propagation waits (5-10 seconds)
   - **Fix:** Use `expect().toContainText()` for error messages

### Medium Priority (Integration Tests)

5. **`tests/e2e/cross-service-integration.spec.ts`** - 7 instances
   - Lines: 109, 291, 323, 338, 354, 370, 386
   - **Pattern:** Service startup waits (5-15 seconds)
   - **Fix:** Use `expect().toHaveText()` or poll API health endpoints

6. **`tests/e2e/integration-performance-enhanced.spec.ts`** - 11 instances
   - Lines: 56, 127, 247, 321, 343, 354, 398, 430, 506
   - **Pattern:** Performance measurement waits
   - **Fix:** Use `expect.poll()` for async conditions

7. **`tests/e2e/frontend-ui-comprehensive.spec.ts`** - 3 instances
   - Lines: 105, 249, 381
   - **Pattern:** UI component loading (10 seconds)
   - **Fix:** Use `expect().toBeVisible()` with timeout

8. **`tests/e2e/dashboard-data-loading.spec.ts`** - 2 instances
   - Lines: 120, 208
   - **Pattern:** Long data loads (10-30 seconds)
   - **Fix:** Use `expect().toContainText()` with higher timeout

### Low Priority (Smoke Tests & Utilities)

9. **`tests/e2e/ai-automation-smoke.spec.ts`** - 1 instance
   - Line: 34
   - **Pattern:** Page load wait
   - **Fix:** Use `expect().toBeVisible()`

10. **`tests/e2e/ai-automation-analysis.spec.ts`** - 2 instances
    - Lines: 240, 297
    - **Pattern:** Analysis completion waits
    - **Fix:** Use `expect().toContainText()`

11. **`tests/e2e/utils/custom-assertions.ts`** - 1 instance
    - Line: 157
    - **Pattern:** Utility function wait
    - **Fix:** Replace with assertion-based wait

12. **`tests/e2e/utils/docker-test-helpers.ts`** - 1 instance
    - Line: 97
    - **Pattern:** Docker container readiness
    - **Fix:** Poll health endpoint instead

13. **`tests/e2e/docker-global-setup.ts`** - 1 instance
    - Line: 72
    - **Pattern:** Global setup wait
    - **Fix:** Use health check polling

---

## Context7 Best Practices Applied

### 1. **Web-First Assertions** (Primary Pattern)
```typescript
// ✅ Automatically retries until condition is met
await expect(locator).toBeVisible();
await expect(locator).toHaveText('expected');
await expect(locator).toHaveClass(/className/);
await expect(page).toHaveURL(/pattern/);
```

### 2. **Polling for Async Conditions**
```typescript
// ✅ For API responses or computed values
await expect.poll(async () => {
  const response = await page.request.get('/api/status');
  return response.status();
}, {
  message: 'API should eventually succeed',
  timeout: 10000,
  intervals: [1000, 2000, 5000]
}).toBe(200);
```

### 3. **Load States for Page Transitions**
```typescript
// ✅ For animations and page loads
await page.waitForLoadState('networkidle');
await page.waitForLoadState('domcontentloaded');
```

### 4. **Explicit Timeouts (When Necessary)**
```typescript
// ✅ Only when no better assertion available
await expect(locator).toBeVisible({ timeout: 5000 });
```

---

## Replacement Patterns by Use Case

### Chart/Graph Updates
```typescript
// ❌ BEFORE
await chartSelector.click();
await page.waitForTimeout(2000);

// ✅ AFTER - Wait for chart to re-render
await chartSelector.click();
await expect(page.locator('canvas')).toBeVisible();
// OR check for data update
await expect(page.locator('[data-testid="chart-data-point"]').first()).toBeVisible();
```

### Theme/UI Changes
```typescript
// ❌ BEFORE
await themeButton.click();
await page.waitForTimeout(1000);

// ✅ AFTER - Wait for class change
await themeButton.click();
await expect(document).toHaveClass(/dark-mode/);
```

### Data Loading
```typescript
// ❌ BEFORE
await refreshButton.click();
await page.waitForTimeout(5000);

// ✅ AFTER - Wait for loading indicator to disappear
await refreshButton.click();
await expect(page.locator('[data-testid="loading-spinner"]')).not.toBeVisible();
await expect(page.locator('[data-testid="data-loaded"]')).toBeVisible();
```

### Animations
```typescript
// ❌ BEFORE
await dialog.click();
await page.waitForTimeout(500); // animation duration

// ✅ AFTER - Wait for animation end state
await dialog.click();
await expect(dialog).toHaveClass(/open/);
// OR use networkidle for complex animations
await page.waitForLoadState('networkidle');
```

### Error Messages
```typescript
// ❌ BEFORE
await submitButton.click();
await page.waitForTimeout(2000);
const error = await page.locator('.error').textContent();

// ✅ AFTER - Wait for error to appear
await submitButton.click();
await expect(page.locator('.error')).toContainText('Invalid input');
```

---

## Benefits of Web-First Assertions

1. **Reliability** - Tests wait exactly as long as needed, no more, no less
2. **Speed** - Tests complete faster (no fixed 2s waits when element appears in 100ms)
3. **Maintainability** - No magic numbers to tune when app performance changes
4. **Clarity** - Assertions describe what we're actually waiting for
5. **Debugging** - Better error messages showing what condition wasn't met

---

## Next Steps

### Immediate (This Session)
1. ✅ Fix `dashboard-functionality.spec.ts` (8/8 complete)
2. ⏳ Create this progress document
3. ⏳ Move to pytest fixes (CRITICAL priority)

### Follow-Up (Next Session)
1. Fix high-priority user-facing tests (performance, visual-regression, monitoring)
2. Fix integration tests with service waits
3. Update utility functions to use polling patterns
4. Run full E2E suite to validate changes

---

## Template for Remaining Fixes

```typescript
// Step 1: Identify what you're waiting for
await page.waitForTimeout(2000); // ❌ What are we actually waiting for?

// Step 2: Replace with appropriate assertion
await expect(page.locator('[data-testid="thing-we-wait-for"]')).toBeVisible();

// Step 3: Add timeout only if default (5s) is insufficient
await expect(page.locator('[data-testid="slow-thing"]')).toBeVisible({ timeout: 10000 });
```

---

## Context7 References

**Source:** `/microsoft/playwright` - Best Practices Documentation

**Key Snippets Used:**
1. "Compare Playwright Web-First Assertions with Manual Checks" - toBeVisible() pattern
2. "Perform Web-First Assertion with toHaveText" - text content waiting
3. "Poll Asynchronous Conditions with expect.poll" - API polling pattern
4. "Perform Playwright Assertions with Auto-Waiting" - comprehensive assertion examples

**Cached:** Yes - Available in `docs/kb/context7-cache/playwright/`


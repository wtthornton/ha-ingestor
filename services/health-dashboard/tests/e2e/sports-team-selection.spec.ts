/**
 * E2E Tests for Sports Team Selection
 * 
 * Tests the complete team selection wizard flow
 */

import { test, expect } from '@playwright/test';

test.describe('Sports Team Selection', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto('http://localhost:3000');
    await page.evaluate(() => localStorage.clear());
    await page.reload();
  });

  test('should show empty state when no teams selected', async ({ page }) => {
    // Navigate to sports tab
    await page.click('button:has-text("🏈 Sports")');

    // Should show empty state
    await expect(page.locator('text=No Teams Selected Yet!')).toBeVisible();
    await expect(page.locator('button:has-text("Add Your First Team")')).toBeVisible();
  });

  test('should open setup wizard on first team add', async ({ page }) => {
    // Navigate to sports tab
    await page.click('button:has-text("🏈 Sports")');

    // Click add team button
    await page.click('button:has-text("Add Your First Team")');

    // Should show setup wizard
    await expect(page.locator('text=Sports Integration Setup')).toBeVisible();
    await expect(page.locator('text=Step 1 of 3')).toBeVisible();
    await expect(page.locator('text=Select NFL Teams')).toBeVisible();
  });

  test('should complete 3-step wizard successfully', async ({ page }) => {
    // Navigate to sports tab and start wizard
    await page.click('button:has-text("🏈 Sports")');
    await page.click('button:has-text("Add Your First Team")');

    // Step 1: Select NFL teams
    await expect(page.locator('text=Step 1 of 3')).toBeVisible();
    
    // Search and select 49ers
    await page.fill('input[placeholder*="Search NFL teams"]', '49ers');
    await page.click('text=SF'); // Click team card
    
    // Verify selection count
    await expect(page.locator('text=/1 NFL team/')).toBeVisible();
    
    // Continue to step 2
    await page.click('button:has-text("Continue")');

    // Step 2: Select NHL teams
    await expect(page.locator('text=Step 2 of 3')).toBeVisible();
    
    // Select Bruins
    await page.click('text=BOS');
    
    // Continue to step 3
    await page.click('button:has-text("Continue")');

    // Step 3: Review
    await expect(page.locator('text=Step 3 of 3')).toBeVisible();
    await expect(page.locator('text=Review Your Selections')).toBeVisible();
    
    // Should show selected teams
    await expect(page.locator('text=San Francisco 49ers')).toBeVisible();
    await expect(page.locator('text=Boston Bruins')).toBeVisible();
    
    // Should show API usage
    await expect(page.locator('text=24 / 100')).toBeVisible(); // 2 teams × 12 = 24
    await expect(page.locator('text=/Within free tier/')).toBeVisible();
    
    // Confirm and complete
    await page.click('button:has-text("Confirm & Start")');

    // Should return to sports tab with teams
    await expect(page.locator('text=Sports Center')).toBeVisible();
    await expect(page.locator('text=2 teams selected')).toBeVisible();
  });

  test('should persist teams in localStorage', async ({ page }) => {
    // Select teams through wizard
    await page.click('button:has-text("🏈 Sports")');
    await page.click('button:has-text("Add Your First Team")');
    await page.click('text=SF');
    await page.click('button:has-text("Continue")');
    await page.click('button:has-text("Continue")'); // Skip NHL
    await page.click('button:has-text("Confirm & Start")');

    // Verify localStorage
    const stored = await page.evaluate(() => 
      localStorage.getItem('sports_selected_teams')
    );
    
    expect(stored).toBeTruthy();
    const parsed = JSON.parse(stored!);
    expect(parsed.nfl_teams).toContain('sf');
    expect(parsed.setup_completed).toBe(true);
  });

  test('should load teams from localStorage on page load', async ({ page }) => {
    // Pre-populate localStorage
    await page.evaluate(() => {
      localStorage.setItem('sports_selected_teams', JSON.stringify({
        nfl_teams: ['dal', 'gb'],
        nhl_teams: ['wsh'],
        setup_completed: true,
        last_updated: new Date().toISOString(),
        version: 1
      }));
    });

    // Reload page
    await page.reload();

    // Navigate to sports tab
    await page.click('button:has-text("🏈 Sports")');

    // Should show teams without wizard
    await expect(page.locator('text=3 teams selected')).toBeVisible();
    await expect(page.locator('text=Sports Center')).toBeVisible();
  });

  test('should allow removing teams through management interface', async ({ page }) => {
    // Setup teams
    await page.evaluate(() => {
      localStorage.setItem('sports_selected_teams', JSON.stringify({
        nfl_teams: ['sf', 'dal'],
        nhl_teams: [],
        setup_completed: true,
        last_updated: new Date().toISOString(),
        version: 1
      }));
    });

    await page.reload();
    await page.click('button:has-text("🏈 Sports")');

    // Open management
    await page.click('button:has-text("Manage Teams")');

    // Should show manage interface
    await expect(page.locator('text=Manage Tracked Teams')).toBeVisible();
    await expect(page.locator('text=2 selected')).toBeVisible();

    // Remove 49ers
    const removeButtons = page.locator('button:has-text("🗑️")');
    await removeButtons.first().click();

    // Should update count
    await expect(page.locator('text=1 selected')).toBeVisible();
  });

  test('should warn when selecting too many teams', async ({ page }) => {
    await page.click('button:has-text("🏈 Sports")');
    await page.click('button:has-text("Add Your First Team")');

    // Select 9 teams (exceeds recommended limit)
    const teams = ['sf', 'dal', 'gb', 'ne', 'kc', 'phi', 'sea', 'den', 'mia'];
    for (const team of teams) {
      const teamButton = page.locator(`text=${team.toUpperCase()}`).first();
      if (await teamButton.isVisible()) {
        await teamButton.click();
      }
    }

    await page.click('button:has-text("Continue")');
    await page.click('button:has-text("Continue")'); // Skip NHL
    
    // Should show warning about high usage
    await expect(page.locator('text=/Approaching free tier limit/')).toBeVisible();
    await expect(page.locator('text=/caution|danger/i')).toBeVisible();
  });

  test('should allow going back to modify selections', async ({ page }) => {
    await page.click('button:has-text("🏈 Sports")');
    await page.click('button:has-text("Add Your First Team")');
    
    // Select team in step 1
    await page.click('text=SF');
    await page.click('button:has-text("Continue")');
    
    // Step 2
    await page.click('text=BOS');
    await page.click('button:has-text("Continue")');
    
    // Step 3 - Go back
    await expect(page.locator('text=Step 3 of 3')).toBeVisible();
    await page.click('button:has-text("Back")');
    
    // Should be back on step 2
    await expect(page.locator('text=Step 2 of 3')).toBeVisible();
    await expect(page.locator('text=Select NHL Teams')).toBeVisible();
  });

  test('should allow skipping NHL selection', async ({ page }) => {
    await page.click('button:has-text("🏈 Sports")');
    await page.click('button:has-text("Add Your First Team")');
    
    await page.click('text=SF');
    await page.click('button:has-text("Continue")');
    
    // Skip NHL
    await page.click('button:has-text("Skip NHL")');
    
    // Should go directly to review
    await expect(page.locator('text=Step 3 of 3')).toBeVisible();
    await expect(page.locator('text=San Francisco 49ers')).toBeVisible();
  });

  test('should filter teams by search query', async ({ page }) => {
    await page.click('button:has-text("🏈 Sports")');
    await page.click('button:has-text("Add Your First Team")');
    
    // Type in search
    await page.fill('input[placeholder*="Search NFL teams"]', 'cowboys');
    
    // Should only show Cowboys
    await expect(page.locator('text=DAL')).toBeVisible();
    await expect(page.locator('text=SF')).not.toBeVisible();
  });
});


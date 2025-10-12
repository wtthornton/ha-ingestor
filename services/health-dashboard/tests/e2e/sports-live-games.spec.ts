/**
 * E2E Tests for Live Games Display
 * 
 * Tests real-time game updates and animations
 */

import { test, expect } from '@playwright/test';

test.describe('Sports Live Games Display', () => {
  test.beforeEach(async ({ page }) => {
    // Setup teams in localStorage
    await page.goto('http://localhost:3000');
    await page.evaluate(() => {
      localStorage.setItem('sports_selected_teams', JSON.stringify({
        nfl_teams: ['sf', 'dal'],
        nhl_teams: ['bos'],
        setup_completed: true,
        last_updated: new Date().toISOString(),
        version: 1
      }));
    });
    await page.reload();
    await page.click('button:has-text("🏈 Sports")');
  });

  test('should display live games when available', async ({ page }) => {
    // Wait for games to load
    await page.waitForSelector('text=Sports Center', { timeout: 5000 });

    // Check for live games section (may or may not have games depending on real data)
    const liveSection = page.locator('text=LIVE NOW');
    const noGamesMessage = page.locator('text=No Games Right Now');

    // Either live games or no games message should be visible
    const hasLiveGames = await liveSection.isVisible();
    const hasNoGames = await noGamesMessage.isVisible();

    expect(hasLiveGames || hasNoGames).toBe(true);
  });

  test('should show upcoming games section', async ({ page }) => {
    await page.waitForSelector('text=Sports Center', { timeout: 5000 });

    // Look for upcoming games or no games message
    const upcomingHeader = page.locator('text=UPCOMING TODAY');
    const noGamesMessage = page.locator('text=No Games Right Now');

    // At least one should be visible
    const hasUpcoming = await upcomingHeader.isVisible();
    const hasNoGames = await noGamesMessage.isVisible();

    expect(hasUpcoming || hasNoGames).toBe(true);
  });

  test('should display team count in header', async ({ page }) => {
    await page.waitForSelector('text=Sports Center', { timeout: 5000 });

    // Should show 3 teams (2 NFL + 1 NHL)
    await expect(page.locator('text=3 Teams')).toBeVisible();
  });

  test('should have refresh button', async ({ page }) => {
    await page.waitForSelector('text=Sports Center', { timeout: 5000 });

    // Check refresh button exists
    const refreshButton = page.locator('button:has-text("🔄")');
    await expect(refreshButton).toBeVisible();

    // Click should work
    await refreshButton.click();
    
    // Should show loading or update timestamp
    await page.waitForTimeout(1000);
  });

  test('should open team management', async ({ page }) => {
    await page.waitForSelector('text=Sports Center', { timeout: 5000 });

    // Click manage teams button
    await page.click('button:has-text("Manage Teams")');

    // Should show management interface
    await expect(page.locator('text=Manage Tracked Teams')).toBeVisible();
    await expect(page.locator('text=2 selected')).toBeVisible(); // NFL teams
    await expect(page.locator('text=1 selected')).toBeVisible(); // NHL teams
  });

  test('should handle loading state gracefully', async ({ page }) => {
    // Navigate quickly to catch loading state
    const loadingSpinner = page.locator('.animate-spin');
    const sportsCenter = page.locator('text=Sports Center');

    // Either loading or content should be visible
    await expect(loadingSpinner.or(sportsCenter)).toBeVisible();
  });

  test('should display last update timestamp', async ({ page }) => {
    await page.waitForSelector('text=Sports Center', { timeout: 5000 });

    // Should show last updated time
    await expect(page.locator('text=/Last updated:/')).toBeVisible();
  });

  test('should show empty state when no teams selected', async ({ page }) => {
    // Clear teams
    await page.evaluate(() => {
      localStorage.setItem('sports_selected_teams', JSON.stringify({
        nfl_teams: [],
        nhl_teams: [],
        setup_completed: false,
        last_updated: new Date().toISOString(),
        version: 1
      }));
    });

    await page.reload();
    await page.click('button:has-text("🏈 Sports")');

    // Should show empty state
    await expect(page.locator('text=No Teams Selected Yet!')).toBeVisible();
  });
});

test.describe('Game Cards', () => {
  test.beforeEach(async ({ page }) => {
    // Setup with teams
    await page.goto('http://localhost:3000');
    await page.evaluate(() => {
      localStorage.setItem('sports_selected_teams', JSON.stringify({
        nfl_teams: ['sf'],
        nhl_teams: [],
        setup_completed: true,
        last_updated: new Date().toISOString(),
        version: 1
      }));
    });
    await page.reload();
    await page.click('button:has-text("🏈 Sports")');
  });

  test('live game card should have action buttons', async ({ page }) => {
    // Wait for content to load
    await page.waitForSelector('text=Sports Center', { timeout: 5000 });

    // Look for live game cards (if any exist)
    const liveGameCard = page.locator('text=LIVE NOW').locator('..').locator('..');
    
    if (await liveGameCard.isVisible()) {
      // Check for action buttons
      await expect(page.locator('button:has-text("Full Stats")')).toBeVisible();
      await expect(page.locator('button:has-text("Watch")')).toBeVisible();
    }
  });

  test('upcoming game card should have notify button', async ({ page }) => {
    await page.waitForSelector('text=Sports Center', { timeout: 5000 });

    // Look for upcoming games
    const upcomingSection = page.locator('text=UPCOMING TODAY');
    
    if (await upcomingSection.isVisible()) {
      await expect(page.locator('button:has-text("Notify")')).toBeVisible();
    }
  });
});


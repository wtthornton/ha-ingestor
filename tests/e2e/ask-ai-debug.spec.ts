/**
 * Debug test for Ask AI
 */

import { test, expect } from '@playwright/test';

test('Debug: Submit query and wait for response', async ({ page }) => {
  // Go to Ask AI page
  await page.goto('http://localhost:3001/ask-ai');
  await page.waitForLoadState('networkidle');
  
  console.log('Page loaded');
  
  // Find input
  const input = page.locator('input[placeholder*="Ask me about"]');
  await expect(input).toBeVisible();
  console.log('Input visible');
  
  // Type query
  await input.fill('Turn on the office lights');
  console.log('Query typed');
  
  // Find and click send button
  const sendButton = page.getByRole('button', { name: /send/i });
  await expect(sendButton).toBeEnabled();
  console.log('Send button enabled');
  
  await sendButton.click();
  console.log('Send button clicked');
  
  // Wait a bit
  await page.waitForTimeout(5000);
  console.log('Waited 5 seconds');
  
  // Check for any toasts
  const body = await page.locator('body').textContent();
  console.log('Page content sample:', body?.substring(0, 500));
  
  // Take screenshot
  await page.screenshot({ path: 'test-results/debug-screenshot.png', fullPage: true });
  console.log('Screenshot saved');
});


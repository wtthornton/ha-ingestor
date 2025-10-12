// Quick test script to verify metrics charts are working
import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('🔍 Testing metrics charts...');
    
    // Clear all browser data and navigate to Docker container
    await page.context().clearCookies();
    await page.goto('http://localhost:3000?_v=' + Date.now());
    await page.waitForLoadState('networkidle');
    
    // Force reload to bypass cache
    await page.reload({ waitUntil: 'networkidle' });
    
    // Wait a bit more for any async loading
    await page.waitForTimeout(2000);
    
    // Click on Services tab
    await page.click('button:has-text("Services")');
    await page.waitForTimeout(1000);
    
    // Click on first "View Details" button
    await page.click('button:has-text("View Details")');
    await page.waitForTimeout(1000);
    
    // Click on Metrics tab
    await page.click('button:has-text("Metrics")');
    await page.waitForTimeout(2000);
    
    // Check if charts are displayed (should not see installation message)
    const installationMessage = await page.locator('text=Installation Required').isVisible();
    const chartTestVisible = await page.locator('text=Chart.js Test').isVisible();
    const chartWorking = await page.locator('text=Chart.js is working').isVisible();
    const chartError = await page.locator('text=Chart.js Error').isVisible();
    
    console.log(`Installation message visible: ${installationMessage}`);
    console.log(`Chart test visible: ${chartTestVisible}`);
    console.log(`Chart working: ${chartWorking}`);
    console.log(`Chart error: ${chartError}`);
    
    // Check if we can see chart elements
    const chartElements = await page.locator('canvas').count();
    console.log(`📊 Found ${chartElements} chart elements`);
    
    // Take a screenshot
    await page.screenshot({ path: 'metrics-charts-test.png' });
    console.log('📸 Screenshot saved as metrics-charts-test.png');
    
    if (!installationMessage && chartTestVisible) {
      if (chartWorking) {
        console.log('✅ Chart.js is working correctly!');
      } else if (chartError) {
        console.log('❌ Chart.js has an error - check console');
      } else {
        console.log('⚠️ Chart test visible but status unclear');
      }
    } else {
      console.log('❌ Charts not working - installation message still showing or chart test not visible');
    }
    
    // Wait a bit to see the charts
    await page.waitForTimeout(3000);
    
  } catch (error) {
    console.error('❌ Error testing metrics charts:', error);
  } finally {
    await browser.close();
  }
})();

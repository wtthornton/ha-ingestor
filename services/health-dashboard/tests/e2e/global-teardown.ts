import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Global Teardown: Cleaning up test environment...');
  
  // Optional: Cleanup test data, close connections, etc.
  
  console.log('✅ Global Teardown Complete');
}

export default globalTeardown;


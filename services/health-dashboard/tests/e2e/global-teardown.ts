import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('Cleaning up global test environment...');
  
  // Add any global cleanup tasks here
  // For example, cleaning up test data, stopping services, etc.
  
  console.log('Global teardown completed');
}

export default globalTeardown;

# Health Dashboard Tests

## Overview

This directory contains unit and integration tests for the Health Dashboard components.

## Setup

### Install Testing Dependencies

```bash
npm install --save-dev vitest @vitest/ui @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

### Update package.json

Add test scripts to `package.json`:

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage"
  }
}
```

### Create vitest.config.ts

Create `vitest.config.ts` in the root of health-dashboard:

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### Create Test Setup File

Create `tests/setup.ts`:

```typescript
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// Cleanup after each test
afterEach(() => {
  cleanup();
});
```

## Running Tests

### Run All Tests

```bash
npm test
```

### Run Tests in Watch Mode

```bash
npm test -- --watch
```

### Run Tests with UI

```bash
npm run test:ui
```

### Run Tests Once (CI Mode)

```bash
npm run test:run
```

### Generate Coverage Report

```bash
npm run test:coverage
```

## Test Structure

```
tests/
├── components/           # Component unit tests
│   ├── ServiceCard.test.tsx
│   ├── ServicesTab.test.tsx
│   └── Dashboard.test.tsx
├── hooks/               # Custom hooks tests
│   ├── useHealth.test.ts
│   └── useStatistics.test.ts
├── services/            # Service layer tests
│   └── api.test.ts
├── setup.ts            # Test setup and configuration
└── README.md           # This file
```

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage for all components
- **Integration Tests**: Critical user flows
- **Snapshot Tests**: UI component consistency

## Writing Tests

### Component Test Example

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ServiceCard } from '../../src/components/ServiceCard';

describe('ServiceCard', () => {
  it('renders service name', () => {
    const mockService = {
      service: 'test-service',
      running: true,
      status: 'running',
    };

    render(<ServiceCard service={mockService} icon="🔧" darkMode={false} />);
    
    expect(screen.getByText('test-service')).toBeInTheDocument();
  });
});
```

### Hook Test Example

```typescript
import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useHealth } from '../../src/hooks/useHealth';

describe('useHealth', () => {
  it('fetches health data', async () => {
    const { result } = renderHook(() => useHealth(30000));

    await waitFor(() => {
      expect(result.current.health).toBeDefined();
      expect(result.current.loading).toBe(false);
    });
  });
});
```

## Best Practices

1. **Use descriptive test names**: Clearly describe what is being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Test user behavior**: Focus on what users see and do
4. **Mock external dependencies**: Use vi.fn() for API calls
5. **Clean up after tests**: Use afterEach for cleanup
6. **Test accessibility**: Include ARIA labels and roles
7. **Test error states**: Include error handling tests
8. **Test loading states**: Verify loading indicators

## Current Test Status

### ServiceCard Component
- ✅ Renders service name and icon
- ✅ Displays port number
- ✅ Shows correct status indicators
- ✅ Displays metrics (uptime, requests, error rate)
- ✅ Handles click events
- ✅ Dark/light mode styling
- ✅ Error message display

### ServicesTab Component
- ✅ Loading state
- ✅ Service data fetching
- ✅ Service grouping (core vs external)
- ✅ Auto-refresh functionality
- ✅ Manual refresh
- ✅ Error handling
- ✅ Dark/light mode styling
- ✅ Empty state handling

## Next Steps

1. Install testing dependencies (see Setup section)
2. Create vitest.config.ts and setup.ts files
3. Run tests: `npm test`
4. Add tests for remaining components
5. Increase coverage to 80%+

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [Testing Library Docs](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest-DOM Matchers](https://github.com/testing-library/jest-dom)


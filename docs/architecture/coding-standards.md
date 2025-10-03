# Coding Standards

### Critical Fullstack Rules

- **Type Sharing:** Always define types in `shared/types/` and import from there
- **API Calls:** Never make direct HTTP calls - use the service layer in `services/`
- **Environment Variables:** Access only through config objects, never `process.env` directly
- **Error Handling:** All API routes must use the standard error handler
- **State Updates:** Never mutate state directly - use proper state management patterns

### Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| Components | PascalCase | - | `HealthDashboard.tsx` |
| Hooks | camelCase with 'use' | - | `useHealthStatus.ts` |
| API Routes | - | kebab-case | `/api/health-status` |
| Database Tables | - | snake_case | `home_assistant_events` |
| Functions | camelCase | snake_case | `getHealthStatus()` / `get_health_status()` |

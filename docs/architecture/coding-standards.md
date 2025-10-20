# Coding Standards

### Critical Fullstack Rules

- **Type Sharing:** Always define types in `shared/types/` and import from there
- **API Calls:** Never make direct HTTP calls - use the service layer in `services/`
- **Environment Variables:** Access only through config objects, never `process.env` directly
- **Error Handling:** All API routes must use the standard error handler
- **State Updates:** Never mutate state directly - use proper state management patterns

### Code Complexity Standards

#### Complexity Thresholds

**Python (Radon):**
- **A (1-5)**: Simple, low risk - **preferred for all new code**
- **B (6-10)**: Moderate complexity - **acceptable**
- **C (11-20)**: Complex - **document thoroughly, refactor when touched**
- **D (21-50)**: Very complex - **refactor as high priority**
- **F (51+)**: Extremely complex - **immediate refactoring required**

**Project Standards:**
- Warn: Complexity > 15
- Error: Complexity > 20
- Target: Average complexity ≤ 5

**TypeScript/JavaScript (ESLint):**
- Max cyclomatic complexity: 15 (warn)
- Max lines per function: 100 (warn)
- Max nesting depth: 4 (warn)
- Max parameters: 5 (warn)
- Max lines per file: 500 (warn)

#### Maintainability Index (Python)
- **A (85-100)**: Highly maintainable - **excellent**
- **B (65-84)**: Moderately maintainable - **acceptable**
- **C (50-64)**: Difficult to maintain - **needs improvement**
- **D/F (0-49)**: Very difficult to maintain - **refactor immediately**

**Project Standard:** Minimum B grade (≥65)

#### Code Duplication
- **Target:** < 3%
- **Warning:** 3-5%
- **Error:** > 5%

**Current Project Metrics (Oct 2025):**
- Python: 0.64% duplication ✅ Excellent
- TypeScript: To be measured

#### When to Refactor vs. Document

**Refactor Immediately If:**
- Complexity > 20 (D/F rating)
- Maintainability < 50 (C/D/F rating)
- Duplication > 5%
- Critical path code with complexity > 15
- Code is actively being modified

**Document Thoroughly If:**
- Complexity 11-20 (C rating) and code is stable
- Complex algorithm that cannot be simplified
- Performance-critical code where simplification would hurt performance
- Legacy code with extensive test coverage (refactoring risk high)
- Domain-specific business logic

**Best Practices:**
- Always document complex code (C rating or higher)
- Plan refactoring when making changes to complex code
- Prefer simplicity over cleverness
- Extract functions when complexity > 10
- Use custom hooks to reduce React component complexity

### Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| Components | PascalCase | - | `HealthDashboard.tsx` |
| Hooks | camelCase with 'use' | - | `useHealthStatus.ts` |
| API Routes | - | kebab-case | `/api/health-status` |
| Database Tables | - | snake_case | `home_assistant_events` |
| Functions | camelCase | snake_case | `getHealthStatus()` / `get_health_status()` |


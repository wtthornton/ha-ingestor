# Python Code Style Guide

## Context

Python-specific code style rules for the ha-ingestor project, extending the global code style guidelines.

## Python-Specific Formatting

### Indentation
- Use **4 spaces** for indentation (Python standard, not 2 spaces as in general guidelines)
- Never use tabs
- Maintain consistent indentation throughout files
- Align nested structures for readability

### Naming Conventions
- **Functions and Variables**: Use snake_case (e.g., `user_profile`, `calculate_total`)
- **Classes and Modules**: Use PascalCase (e.g., `UserProfile`, `PaymentProcessor`)
- **Constants**: Use UPPER_SNAKE_CASE (e.g., `MAX_RETRY_COUNT`)
- **Private Methods**: Use leading underscore (e.g., `_internal_helper`)
- **Protected Methods**: Use leading underscore (e.g., `_protected_method`)
- **Magic Methods**: Use double underscores (e.g., `__init__`, `__str__`)

### String Formatting
- Use f-strings for string interpolation: `f"Hello {name}"`
- Use single quotes for simple strings: `'Hello World'`
- Use double quotes when the string contains single quotes
- Use triple quotes for multi-line strings and docstrings

### Code Comments and Documentation
- Use docstrings for all public functions, classes, and modules
- Follow Google docstring format or NumPy docstring format consistently
- Add brief comments above non-obvious business logic
- Document complex algorithms or calculations
- Explain the "why" behind implementation choices
- Never remove existing comments unless removing the associated code
- Update comments when modifying code to maintain accuracy
- Keep comments concise and relevant

### Import Organization
- Group imports in this order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- Separate each group with a blank line
- Use absolute imports for external packages
- Use relative imports within the package
- Avoid wildcard imports (`from module import *`)
- Import specific items: `from module import specific_item`

### Type Hints
- Use type hints for all function parameters and return values
- Use type hints for class attributes
- Use `typing` module for complex types (List, Dict, Optional, etc.)
- Use `Union` or `|` for union types (Python 3.10+)
- Use `Any` sparingly and document why it's necessary

### Async/Await Patterns
- Use `async def` for async functions
- Use `await` for async operations
- Use `asyncio.gather()` for concurrent operations
- Handle async context managers properly
- Use `asyncio.create_task()` for fire-and-forget operations

### Error Handling
- Use specific exception types, not generic `Exception`
- Create custom exception classes for business logic errors
- Use context managers (`with` statements) for resource management
- Implement proper cleanup in finally blocks
- Log errors with appropriate context and stack traces

### Performance Considerations
- Use list comprehensions over explicit loops when appropriate
- Use `enumerate()` instead of range(len()) for indexed iteration
- Use `in` operator for membership testing
- Use `set` for fast lookups when order doesn't matter
- Use `collections.defaultdict` when appropriate
- Profile code before optimizing

### Testing Patterns
- Use descriptive test method names
- Use fixtures for common test data
- Mock external dependencies
- Test both success and failure cases
- Use parametrized tests for multiple scenarios
- Test edge cases and boundary conditions

### Logging
- Use structured logging with appropriate log levels
- Include relevant context in log messages
- Use correlation IDs for request tracing
- Avoid logging sensitive information
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Configuration Management
- Use Pydantic for configuration validation
- Support environment variable overrides
- Use type-safe configuration objects
- Validate configuration at startup
- Provide sensible defaults

### Security
- Validate all input data
- Use parameterized queries for database operations
- Sanitize user inputs
- Use secure random number generators
- Follow OWASP guidelines for web applications

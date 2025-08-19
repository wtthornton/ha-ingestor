# 🤝 Contributing to ha-ingestor

Thank you for your interest in contributing to ha-ingestor! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** for your changes
4. **Make your changes** following our coding standards
5. **Test your changes** thoroughly
6. **Submit a pull request** with a clear description

## 🏗️ Development Setup

### Prerequisites
- **Python 3.12+**
- **Poetry** for dependency management
- **Git** for version control
- **Docker** (optional, for containerized development)

### Local Setup
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ha-ingestor.git
cd ha-ingestor

# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Activate virtual environment
poetry shell
```

### Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env with your configuration
# Required: MQTT credentials, InfluxDB settings
# Optional: Logging, monitoring settings
```

## 📝 Coding Standards

### Python Style Guide
- Follow **PEP 8** with project-specific overrides
- Use **4 spaces** for indentation (no tabs)
- Maximum line length: **88 characters** (Black default)
- Use **snake_case** for functions and variables
- Use **PascalCase** for classes
- Use **UPPER_SNAKE_CASE** for constants

### Type Hints
- **Always use type hints** for function parameters and return values
- Use **Union types** (e.g., `str | None`) for optional values
- Use **TypedDict** for complex dictionary structures
- Import types from `typing` module when needed

### Example
```python
from typing import Any, Dict, List, Optional

def process_event(
    event_data: Dict[str, Any],
    filters: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Process an event through the filter chain.

    Args:
        event_data: Raw event data from Home Assistant
        filters: Optional list of filter names to apply

    Returns:
        Processed event data
    """
    # Implementation here
    pass
```

### Documentation
- **Docstrings** for all public functions and classes
- Use **Google-style docstrings** with type hints
- Include **examples** for complex functions
- Document **exceptions** that may be raised

### Example Docstring
```python
def create_filter_chain(
    filter_configs: List[Dict[str, Any]]
) -> FilterChain:
    """Create a filter chain from configuration.

    Args:
        filter_configs: List of filter configuration dictionaries

    Returns:
        Configured FilterChain instance

    Raises:
        ValueError: If filter configuration is invalid
        FilterError: If filter creation fails

    Example:
        >>> configs = [{"type": "domain", "domains": ["light"]}]
        >>> chain = create_filter_chain(configs)
        >>> isinstance(chain, FilterChain)
        True
    """
    pass
```

## 🧪 Testing

### Test Structure
- **Unit tests** in `tests/unit/` directory
- **Integration tests** in `tests/` directory
- **Test files** should be named `test_*.py`
- **Test functions** should be named `test_*`

### Running Tests
```bash
# Run all tests
poetry run pytest

# Run specific test categories
poetry run pytest -m unit          # Unit tests only
poetry run pytest -m integration   # Integration tests only
poetry run pytest -m performance   # Performance tests only

# Run with coverage
poetry run pytest --cov=ha_ingestor --cov-report=html

# Run specific test file
poetry run pytest tests/test_filters.py

# Run specific test function
poetry run pytest tests/test_filters.py::test_domain_filter
```

### Writing Tests
- **Test one thing** per test function
- Use **descriptive test names** that explain the behavior
- **Mock external dependencies** (network calls, file I/O)
- Use **fixtures** for common test data
- **Assert specific conditions** rather than just checking for no exceptions

### Example Test
```python
import pytest
from unittest.mock import Mock, patch
from ha_ingestor.filters.domain_filter import DomainFilter

class TestDomainFilter:
    """Test DomainFilter functionality."""

    def test_domain_filter_accepts_matching_domain(self):
        """Test that domain filter accepts events with matching domain."""
        # Arrange
        filter_config = {"domains": ["light", "switch"]}
        domain_filter = DomainFilter("test_filter", filter_config)
        event_data = {"domain": "light", "entity_id": "light.living_room"}

        # Act
        result = domain_filter.filter(event_data)

        # Assert
        assert result.accepted is True
        assert result.reason is None

    def test_domain_filter_rejects_non_matching_domain(self):
        """Test that domain filter rejects events with non-matching domain."""
        # Arrange
        filter_config = {"domains": ["light", "switch"]}
        domain_filter = DomainFilter("test_filter", filter_config)
        event_data = {"domain": "sensor", "entity_id": "sensor.temperature"}

        # Act
        result = domain_filter.filter(event_data)

        # Assert
        assert result.accepted is False
        assert "domain 'sensor' not in allowed domains" in result.reason
```

## 🔍 Code Quality

### Pre-commit Hooks
We use pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run all hooks on staged files
poetry run pre-commit run

# Run all hooks on all files
poetry run pre-commit run --all-files
```

### Manual Quality Checks
```bash
# Format code with Black
poetry run black .

# Check code formatting
poetry run black --check --diff .

# Run Ruff linter
poetry run ruff check .

# Run MyPy type checker
poetry run mypy ha_ingestor/

# Run all quality checks
poetry run pre-commit run --all-files
```

### Quality Standards
- **All tests must pass** before submitting PR
- **Pre-commit hooks must pass** (Black, Ruff, MyPy)
- **Code coverage** should not decrease significantly
- **No new warnings** should be introduced

## 📋 Pull Request Process

### Before Submitting
1. **Ensure all tests pass** locally
2. **Run pre-commit hooks** and fix any issues
3. **Update documentation** if needed
4. **Add tests** for new functionality
5. **Update CHANGELOG.md** with your changes

### Pull Request Template
Use the provided PR template and fill in all sections:
- **Description** of what the PR accomplishes
- **Related issues** that this PR addresses
- **Changes made** checklist
- **Testing** checklist
- **Environment** information

### Review Process
1. **Automated checks** must pass (CI/CD pipeline)
2. **Code review** by maintainers
3. **Address feedback** and make requested changes
4. **Maintainer approval** required for merge

## 🐛 Bug Reports

### Before Reporting
1. **Search existing issues** to avoid duplicates
2. **Check documentation** for solutions
3. **Test with latest version** from master branch
4. **Reproduce the issue** consistently

### Bug Report Template
Use the provided bug report template and include:
- **Clear description** of the bug
- **Steps to reproduce** the issue
- **Expected vs. actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Error messages** and stack traces
- **Minimal reproduction case** if possible

## 🚀 Feature Requests

### Before Requesting
1. **Check existing issues** for similar requests
2. **Review the roadmap** in `.agent-os/product/roadmap.md`
3. **Consider the scope** and impact
4. **Think about implementation** approach

### Feature Request Template
Use the provided feature request template and include:
- **Clear description** of the feature
- **Problem statement** it solves
- **Proposed solution** approach
- **Use cases** and examples
- **Feature category** classification

## 🏷️ Issue Labels

We use the following labels to categorize issues:

- **`bug`** - Something isn't working
- **`enhancement`** - New feature or request
- **`documentation`** - Improvements or additions to documentation
- **`good first issue`** - Good for newcomers
- **`help wanted`** - Extra attention is needed
- **`needs-triage`** - Needs initial review
- **`priority: high`** - High priority issues
- **`priority: low`** - Low priority issues

## 📚 Additional Resources

- **`.agent-os/product/`** - Product planning and roadmap
- **`.agent-os/specs/`** - Technical specifications
- **`DEVELOPMENT.md`** - Development setup guide
- **`README.md`** - Project overview and quick start
- **GitHub Issues** - Browse existing issues and discussions

## 🤝 Community Guidelines

- **Be respectful** and inclusive in all interactions
- **Help others** by answering questions and providing guidance
- **Share knowledge** and contribute to documentation
- **Follow the project's** coding standards and practices
- **Provide constructive feedback** in reviews and discussions

## 📞 Getting Help

- **GitHub Issues** - For bugs, feature requests, and questions
- **GitHub Discussions** - For general questions and community discussions
- **Pull Requests** - For code contributions and improvements

Thank you for contributing to ha-ingestor! 🎉

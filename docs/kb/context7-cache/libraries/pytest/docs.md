# pytest Documentation Cache

## Overview
pytest is a mature full-featured Python testing framework that helps you write better programs. This cache contains focused documentation on testing, fixtures, and parametrization.

## Testing Framework Fundamentals

### Core Concepts
- **Test discovery**: Automatic test finding
- **Assertion introspection**: Detailed failure reporting
- **Fixture system**: Dependency injection
- **Plugin architecture**: Extensible framework
- **Parametrization**: Data-driven testing
- **Parallel execution**: Concurrent test running

### Test Structure
- **Test functions**: Individual test cases
- **Test classes**: Grouped test methods
- **Test modules**: Test file organization
- **Test packages**: Hierarchical test structure
- **Test directories**: Project-wide test organization
- **Naming conventions**: Test identification patterns

### Assertion System
- **Built-in assertions**: Python assert statements
- **Assertion helpers**: pytest-specific assertions
- **Custom assertions**: User-defined assertion functions
- **Assertion introspection**: Detailed error messages
- **Assertion rewriting**: Enhanced assert statements
- **Failure reporting**: Comprehensive error display

## Fixture Management

### Fixture Basics
- **Fixture definition**: Creating reusable components
- **Fixture scope**: Lifetime management
- **Fixture dependencies**: Dependent fixtures
- **Fixture parametrization**: Multiple fixture instances
- **Fixture autouse**: Automatic fixture usage
- **Fixture cleanup**: Resource management

### Fixture Scopes
- **Function scope**: Per-test fixture instances
- **Class scope**: Per-class fixture instances
- **Module scope**: Per-module fixture instances
- **Package scope**: Per-package fixture instances
- **Session scope**: Per-session fixture instances
- **Dynamic scope**: Runtime scope determination

### Advanced Fixtures
- **Parametrized fixtures**: Multiple fixture values
- **Indirect parametrization**: Fixture parameter passing
- **Fixture factories**: Dynamic fixture creation
- **Conditional fixtures**: Context-dependent fixtures
- **Fixture composition**: Combining multiple fixtures
- **Fixture inheritance**: Fixture reuse patterns

## Test Parametrization

### Basic Parametrization
- **@pytest.mark.parametrize**: Function parametrization
- **Parameter values**: Test data specification
- **Parameter names**: Descriptive parameter labels
- **Parameter combinations**: Multiple parameter sets
- **Parameter types**: Various data types
- **Parameter validation**: Input validation

### Advanced Parametrization
- **Indirect parametrization**: Fixture parameter passing
- **Parametrize with fixtures**: Fixture-based parametrization
- **Dynamic parametrization**: Runtime parameter generation
- **Parametrize with marks**: Conditional test execution
- **Parametrize with ids**: Custom test identification
- **Parametrize with scope**: Parameter scope management

### Data-Driven Testing
- **External data sources**: File-based test data
- **Database integration**: Database-driven testing
- **API data**: External API test data
- **Generated data**: Programmatically created test data
- **Random data**: Randomized test inputs
- **Combinatorial testing**: All parameter combinations

## Test Discovery and Execution

### Test Discovery
- **Automatic discovery**: Finding test files and functions
- **Custom collection**: Custom test discovery rules
- **Test markers**: Test categorization
- **Test selection**: Running specific tests
- **Test filtering**: Conditional test execution
- **Test grouping**: Logical test organization

### Execution Options
- **Verbose output**: Detailed test execution information
- **Quiet mode**: Minimal output
- **Stop on failure**: Early test termination
- **Parallel execution**: Concurrent test running
- **Test timeouts**: Time-limited test execution
- **Test retries**: Automatic retry on failure

### Test Reporting
- **Console output**: Terminal-based reporting
- **HTML reports**: Web-based test reports
- **XML reports**: Machine-readable test results
- **JSON reports**: Structured test data
- **Custom reporters**: User-defined reporting
- **Integration**: CI/CD system integration

## Advanced Features

### Plugins and Extensions
- **Plugin system**: Framework extension
- **Built-in plugins**: Core functionality
- **Third-party plugins**: Community extensions
- **Custom plugins**: User-created extensions
- **Plugin configuration**: Plugin setup and tuning
- **Plugin management**: Plugin lifecycle

### Mocking and Patching
- **unittest.mock integration**: Mock object support
- **Patching**: Object replacement
- **Spying**: Method call monitoring
- **Stubbing**: Return value control
- **Mock validation**: Mock usage verification
- **Async mocking**: Asynchronous mock support

### Performance Testing
- **Timing tests**: Performance measurement
- **Memory profiling**: Resource usage monitoring
- **Benchmarking**: Performance comparison
- **Load testing**: Stress testing support
- **Profiling integration**: Performance analysis
- **Resource monitoring**: System resource tracking

## Best Practices
- **Test organization**: Logical test structure
- **Test naming**: Descriptive test names
- **Test isolation**: Independent test execution
- **Fixture design**: Efficient fixture usage
- **Error handling**: Robust error management
- **Documentation**: Clear test documentation

# Context7 Standards for ha-ingestor

## Overview
This document defines Context7-specific standards and patterns for the ha-ingestor project, complementing the existing standards in this directory.

## 🎯 **Context7 Integration Standards**

### **1. Project Structure Compliance**
- **Required**: All new features must follow Context7 patterns
- **Required**: Use established base classes from examples
- **Required**: Follow async-first architecture patterns
- **Required**: Implement proper error handling and logging

### **2. AI Development Workflow**
- **Step 1**: Always start with `.agent-os/instructions/ai-development.md`
- **Step 2**: Reference established patterns from examples
- **Step 3**: Follow Context7 standards for consistency
- **Step 4**: Document new patterns in Context7 structure

### **3. Code Organization Standards**
- **Filters**: Must extend `ha_ingestor.filters.base.BaseFilter`
- **Transformers**: Must extend `ha_ingestor.transformers.base.Transformer`
- **Models**: Must use Pydantic for validation
- **Configuration**: Must follow environment variable conventions

## 🔧 **Context7 Implementation Standards**

### **Filter Implementation**
```python
from ha_ingestor.filters.base import BaseFilter

class CustomFilter(BaseFilter):
    """AI ASSISTANT CONTEXT: Custom filter implementation."""

    async def filter(self, event) -> bool:
        """Filter logic implementation."""
        # Use established patterns from examples
        pass
```

### **Transformer Implementation**
```python
from ha_ingestor.transformers.base import Transformer

class CustomTransformer(Transformer):
    """AI ASSISTANT CONTEXT: Custom transformer implementation."""

    async def transform(self, event):
        """Transform logic implementation."""
        # Use established patterns from examples
        pass
```

### **Configuration Management**
```python
from pydantic import BaseSettings

class CustomConfig(BaseSettings):
    """AI ASSISTANT CONTEXT: Configuration management."""

    # Follow environment variable conventions
    custom_setting: str = "default"

    class Config:
        env_prefix = "HA_INGESTOR_"
```

## 📚 **Context7 Documentation Standards**

### **Required Documentation**
- **AI ASSISTANT CONTEXT**: All public classes and methods
- **Implementation Examples**: Reference to examples directory
- **Pattern Usage**: Clear indication of established patterns
- **Related Files**: Links to related implementation files

### **Documentation Format**
```python
class ExampleClass:
    """
    AI ASSISTANT CONTEXT: Brief description of purpose and patterns.

    Key Patterns Used:
    - Async-first architecture
    - Pipeline processing
    - Error handling with retry logic

    Common Modifications:
    - Configuration changes
    - Filter adjustments
    - Transformer modifications

    Related Files:
    - examples/common_patterns_demo.py
    - ha_ingestor/pipeline.py
    """
```

## 🚀 **Context7 Quality Standards**

### **Code Quality Requirements**
- **Type Hints**: Required for all functions and methods
- **Async Support**: All I/O operations must be async
- **Error Handling**: Use established retry and logging patterns
- **Testing**: Must include unit tests with async support

### **Performance Standards**
- **Async Operations**: Use `asyncio.gather()` for concurrent operations
- **Batch Processing**: Implement batch operations for InfluxDB writes
- **Connection Pooling**: Use established connection management patterns
- **Memory Management**: Follow established memory optimization patterns

### **Security Standards**
- **Input Validation**: Use Pydantic for all input validation
- **Environment Variables**: Sensitive data in environment variables only
- **Authentication**: Follow established authentication patterns
- **Error Messages**: No sensitive information in error messages

## 📈 **Context7 Compliance Metrics**

### **Compliance Checklist**
- [ ] Follows Context7 AI development workflow
- [ ] Uses established base classes and patterns
- [ ] Implements proper error handling and logging
- [ ] Includes comprehensive AI ASSISTANT CONTEXT documentation
- [ ] Follows async-first architecture patterns
- [ ] Uses Pydantic for configuration and validation
- [ ] Includes proper type hints throughout
- [ ] Follows established testing patterns

### **Quality Score Calculation**
- **Context7 Workflow**: 25%
- **Pattern Usage**: 25%
- **Documentation**: 20%
- **Code Quality**: 20%
- **Testing**: 10%

## 🎯 **Context7 Evolution Standards**

### **When Adding New Patterns**
1. **Document in examples**: Add to `examples/common_patterns_demo.py`
2. **Update Context7**: Add to appropriate Context7 standards
3. **Share learnings**: Update `.agent-os/standards/` files
4. **Maintain consistency**: Ensure new patterns align with existing ones

### **When Updating Standards**
1. **Review impact**: Assess impact on existing implementations
2. **Update documentation**: Keep all Context7 files current
3. **Communicate changes**: Update AI development instructions
4. **Maintain backward compatibility**: Don't break existing patterns

## 🔍 **Context7 Validation**

### **Automated Checks**
- **Pre-commit hooks**: Ensure Context7 compliance
- **Type checking**: MyPy validation for type hints
- **Code formatting**: Black and Ruff for consistency
- **Documentation**: Ensure AI ASSISTANT CONTEXT presence

### **Manual Reviews**
- **Context7 workflow**: Verify proper Context7 usage
- **Pattern compliance**: Check established pattern usage
- **Documentation quality**: Review AI ASSISTANT CONTEXT clarity
- **Integration testing**: Verify Context7 pattern integration

## 🎉 **Context7 Standards Summary**

### **Key Principles**
1. **Always start with Context7**: Check `.agent-os/` first
2. **Use established patterns**: Don't reinvent the wheel
3. **Document everything**: Maintain AI ASSISTANT CONTEXT
4. **Maintain consistency**: Follow established standards
5. **Evolve thoughtfully**: Update Context7 based on learnings

### **Expected Outcomes**
- **Faster AI development**: Reduced research time
- **Higher quality code**: Consistent patterns and standards
- **Better maintainability**: Clear documentation and patterns
- **Improved collaboration**: Shared understanding and standards

---

**Context7 Standards Level**: Enhanced (9/10)
**Compliance Requirements**: High
**Quality Expectations**: Excellence
**Development Velocity**: Maximum

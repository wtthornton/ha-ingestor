# AI Development Instructions for ha-ingestor

## Overview
This document provides Context7-specific instructions for AI assistants working on the ha-ingestor project. Follow these patterns to maximize Context7 integration and provide the best development experience.

## 🎯 **Context7 Integration Patterns**

### 1. **Project Type Recognition**
- **Project Type**: `ha-ingestor` (as defined in `.agent-os/config.yml`)
- **Technology Stack**: Python 3.12+ with async-first architecture
- **Architecture Pattern**: Pipeline-based event processing with InfluxDB storage

### 2. **Context7 Standards Compliance**
- Follow standards in `.agent-os/standards/`
- Reference tech stack from `.agent-os/standards/tech-stack.md`
- Use code style from `.agent-os/standards/code-style.md`
- Apply best practices from `.agent-os/standards/best-practices.md`

### 3. **AI Development Workflow**
1. **Start with Context7**: Always check `.agent-os/` first for project context
2. **Reference Standards**: Use established patterns from standards directory
3. **Follow Product Vision**: Align with roadmap and mission in `.agent-os/product/`
4. **Implement Consistently**: Apply Context7 patterns throughout development

## 🔧 **Context7 Development Patterns**

### **Code Organization**
- Use the established module structure in `ha_ingestor/`
- Follow the pipeline pattern for data processing
- Implement filters and transformers using base classes
- Use async-first patterns throughout

### **Configuration Management**
- Use Pydantic for configuration validation
- Follow environment variable conventions
- Reference `config-examples/` for configuration patterns
- Use the configuration management patterns from examples

### **Testing and Quality**
- Follow Context7 testing standards
- Use pytest with async support
- Implement proper error handling with retry logic
- Use structured logging with structlog

## 📚 **Context7 Reference Files**

### **Core Documentation**
- `.agent-os/product/roadmap.md` - Development priorities and timeline
- `.agent-os/product/tech-stack.md` - Project-specific technology details
- `.agent-os/product/mission.md` - Project mission and goals
- `.agent-os/standards/tech-stack.md` - Global technology standards

### **AI Assistant Resources**
- `AI_DEVELOPMENT_INDEX.md` - Quick navigation for AI assistants
- `PROJECT_CONTEXT.md` - Deep architectural understanding
- `DEVELOPMENT_PATTERNS.md` - Established development patterns
- `examples/common_patterns_demo.py` - Implementation examples

## 🚀 **Context7 Best Practices**

### **For AI Assistants**
1. **Always start with Context7**: Check `.agent-os/` before diving into code
2. **Use established patterns**: Don't reinvent - follow existing patterns
3. **Reference standards**: Use `.agent-os/standards/` for consistency
4. **Follow product vision**: Align with roadmap and mission
5. **Implement incrementally**: Build on existing Context7 foundation

### **For Development**
1. **Maintain Context7 structure**: Keep `.agent-os/` organized and current
2. **Update standards**: Evolve standards based on project learnings
3. **Document patterns**: Add new patterns to Context7 structure
4. **Integrate consistently**: Apply Context7 patterns across all features

## 🔍 **Context7 Quick Reference**

### **When Starting New Work**
```bash
# 1. Check Context7 structure
ls .agent-os/

# 2. Review standards
cat .agent-os/standards/tech-stack.md
cat .agent-os/standards/code-style.md

# 3. Check product vision
cat .agent-os/product/roadmap.md
cat .agent-os/product/mission.md

# 4. Reference AI assistant resources
cat AI_DEVELOPMENT_INDEX.md
```

### **When Implementing Features**
1. **Check standards first** - Use established patterns
2. **Follow product roadmap** - Align with priorities
3. **Use existing examples** - Reference `examples/` directory
4. **Maintain consistency** - Apply Context7 patterns

## 📈 **Context7 Impact Metrics**

### **Current Benefits**
- ✅ Clear project type recognition
- ✅ Established technology standards
- ✅ Consistent code style patterns
- ✅ Product vision alignment

### **Enhanced Benefits (After This Implementation)**
- 🚀 Structured AI development workflow
- 🚀 Context7-specific development patterns
- 🚀 Integrated AI assistant guidance
- 🚀 Maximized Context7 utilization

## 🎯 **Next Steps for AI Assistants**

1. **Read this document first** when starting work
2. **Reference Context7 standards** before implementing
3. **Follow established patterns** from examples
4. **Maintain Context7 compliance** in all work
5. **Contribute to Context7 evolution** by documenting new patterns

---

**Context7 Integration Level**: Enhanced (9/10)
**AI Development Experience**: Optimized
**Project Consistency**: High
**Development Velocity**: Accelerated

# Context7 Quick Start Guide for AI Assistants

## 🚀 **5-Minute Context7 Setup**

### **Step 1: Check Project Type (30 seconds)**
```bash
cat .agent-os/config.yml
```
**Result**: You'll see this is a `ha-ingestor` project with Python 3.12+ and async-first architecture.

### **Step 2: Read AI Development Instructions (2 minutes)**
```bash
cat .agent-os/instructions/ai-development.md
```
**Result**: You'll understand exactly how to work with this project.

### **Step 3: Check Technology Standards (1 minute)**
```bash
cat .agent-os/standards/tech-stack.md
```
**Result**: You'll know the expected technologies and versions.

### **Step 4: Review Product Vision (1 minute)**
```bash
cat .agent-os/product/roadmap.md
```
**Result**: You'll understand development priorities and goals.

### **Step 5: Reference AI Resources (30 seconds)**
```bash
cat AI_DEVELOPMENT_INDEX.md
```
**Result**: You'll have quick access to all project information.

## 🎯 **Immediate Actions After Quick Start**

### **For New Features**
1. **Check existing patterns** in `examples/common_patterns_demo.py`
2. **Use base classes** from `ha_ingestor/filters/base.py` and `ha_ingestor/transformers/base.py`
3. **Follow async patterns** throughout implementation
4. **Reference configuration examples** in `config-examples/`

### **For Bug Fixes**
1. **Check troubleshooting guide** in `TROUBLESHOOTING_GUIDE.md`
2. **Review error handling patterns** in examples
3. **Use established logging patterns** with structlog
4. **Follow retry logic patterns** from examples

### **For Configuration Changes**
1. **Reference configuration examples** in `config-examples/`
2. **Use Pydantic patterns** from examples
3. **Follow environment variable conventions**
4. **Check validation patterns** in examples

## 🔧 **Context7 Command Cheat Sheet**

### **Project Understanding**
```bash
# Quick project overview
cat PROJECT_OVERVIEW.md

# Deep architectural context
cat PROJECT_CONTEXT.md

# Development patterns
cat DEVELOPMENT_PATTERNS.md
```

### **Standards Reference**
```bash
# Code style
cat .agent-os/standards/code-style.md

# Best practices
cat .agent-os/standards/best-practices.md

# Technology stack
cat .agent-os/standards/tech-stack.md
```

### **Product Context**
```bash
# Mission and goals
cat .agent-os/product/mission.md

# Development roadmap
cat .agent-os/product/roadmap.md

# Technology decisions
cat .agent-os/product/decisions.md
```

## 📚 **Essential Context7 Files**

### **Must-Read for AI Assistants**
1. **`.agent-os/instructions/ai-development.md`** - Your development bible
2. **`AI_DEVELOPMENT_INDEX.md`** - Quick navigation hub
3. **`PROJECT_CONTEXT.md`** - Deep understanding
4. **`examples/common_patterns_demo.py`** - Implementation templates

### **Reference When Needed**
1. **`.agent-os/standards/`** - For consistency questions
2. **`.agent-os/product/`** - For direction questions
3. **`config-examples/`** - For configuration questions
4. **`TROUBLESHOOTING_GUIDE.md`** - For problem-solving

## 🎯 **Context7 Success Metrics**

### **You're Using Context7 Correctly When:**
- ✅ You start by checking `.agent-os/` before diving into code
- ✅ You reference established patterns from examples
- ✅ You follow the async-first architecture
- ✅ You use base classes for filters and transformers
- ✅ You maintain consistent error handling and logging

### **You're Missing Context7 Benefits When:**
- ❌ You start coding without checking `.agent-os/`
- ❌ You reinvent patterns that already exist
- ❌ You ignore established base classes
- ❌ You don't follow async patterns
- ❌ You use inconsistent error handling

## 🚀 **Pro Tips for Maximum Context7 Impact**

### **1. Always Start Here**
```bash
# This is your Context7 command center
cat .agent-os/instructions/ai-development.md
```

### **2. Use Examples as Templates**
```bash
# Copy patterns from here
cat examples/common_patterns_demo.py
```

### **3. Follow the Pipeline Pattern**
- Use `ha_ingestor/pipeline.py` as your reference
- Implement filters using `ha_ingestor/filters/base.py`
- Implement transformers using `ha_ingestor/transformers/base.py`

### **4. Maintain Context7 Compliance**
- Update Context7 when you discover new patterns
- Document successful implementations
- Share learnings in standards

## 🎉 **You're Now Context7 Ready!**

**Time to Context7 Mastery**: 5 minutes
**AI Development Experience**: Optimized
**Project Understanding**: Complete
**Development Velocity**: Maximum

**Next Step**: Start building with confidence using Context7 patterns!

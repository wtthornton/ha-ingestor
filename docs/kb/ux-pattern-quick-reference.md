# UX/UI Pattern Quick Reference

## 🎨 Preferred Patterns for HA Ingestor

This document provides quick access to approved UI/UX patterns for the project.

---

## ✅ Service Visualization: Dependencies Tab Pattern

**Status:** ✅ Production-tested, User-approved  
**Source:** http://localhost:3000/ - Dependencies Tab  
**Full Documentation:** [context7-cache/ux-patterns/health-dashboard-dependencies-tab-pattern.md](context7-cache/ux-patterns/health-dashboard-dependencies-tab-pattern.md)

### Quick Summary

Interactive service dependency graph with visual layers, click-to-highlight, and status indicators.

### When to Use

- Service topology visualizations
- Data flow diagrams
- System architecture views
- Microservice dependency graphs
- Pipeline visualizations
- Infrastructure maps

### Key Features

✨ **Interactive** - Click to highlight dependencies  
🎯 **Hover tooltips** - Contextual information on hover  
📊 **Layered layout** - Top-to-bottom data flow  
🎨 **Status colors** - Green/Yellow/Red/Gray indicators  
😊 **Icon-based** - Emoji icons for quick recognition  
✨ **Animations** - Smooth scale transforms  
🌙 **Dark mode** - Full theme support  
📱 **Responsive** - Grid layouts adapt to screen size  
⚡ **Lightweight** - Pure React/CSS, no heavy libraries  

### Technology Stack

```
React 18.2
TypeScript 5.2
Tailwind CSS 3.4
Vite 5.0
```

### Quick Implementation Pattern

```typescript
// Node with click-to-highlight
<div
  onClick={handleNodeClick}
  onMouseEnter={handleHover}
  className={`
    px-6 py-4 rounded-lg border-2 cursor-pointer transition-all
    ${statusColor}
    ${isHighlighted ? 'ring-4 ring-blue-500 scale-110' : 'hover:scale-105'}
  `}
>
  <div className="text-3xl">{icon}</div>
  <div className="text-sm">{name}</div>
</div>
```

### Status Color Pattern

```typescript
const colors = {
  running: 'bg-green-900 border-green-700',  // or light mode variant
  error: 'bg-red-900 border-red-700',
  degraded: 'bg-yellow-900 border-yellow-700',
  unknown: 'bg-gray-700 border-gray-600'
};
```

### Performance

- **No heavy graph libraries** (D3, Vis.js)
- **Pure React/CSS** implementation
- **Minimal re-renders** with state management
- **Fast interactions** (<50ms response)

---

## 📋 Pattern Catalog

| Pattern | Status | Use For | Complexity |
|---------|--------|---------|------------|
| **Dependencies Tab** | ✅ Approved | Service graphs, data flow | Medium |
| *More patterns coming soon* | | | |

---

## 🔍 Finding Patterns

### Context7 KB Commands

```bash
# Search for patterns
*context7-kb-search "dependencies visualization"
*context7-kb-search "service graph"
*context7-kb-search "interactive visualization"

# View KB status
*context7-kb-status

# View all patterns
*context7-kb-search "ux-patterns"
```

### Direct Access

- **Pattern Catalog:** `docs/kb/context7-cache/ux-patterns/README.md`
- **KB Index:** `docs/kb/context7-cache/index.yaml`
- **This Reference:** `docs/kb/ux-pattern-quick-reference.md`

---

## 💡 Design Principles

When implementing any pattern, follow these core principles:

1. **Visual Hierarchy** - Most important info is most prominent
2. **Progressive Enhancement** - Works without interaction, better with it
3. **Feedback Loop** - Every interaction provides visual feedback
4. **Consistency** - Same patterns throughout (colors, spacing, transitions)
5. **Clarity** - No ambiguity in what each element represents
6. **Performance** - Lightweight, no unnecessary work
7. **Accessibility** - Keyboard nav, ARIA labels, high contrast

---

## 🚀 Contributing New Patterns

When you discover a great UI/UX pattern:

1. **Document it thoroughly** using the pattern template
2. **Include code examples** for reusability
3. **Add to KB index** (`docs/kb/context7-cache/index.yaml`)
4. **Update this reference** with quick access info
5. **Create memory** so it's remembered for future use

### Pattern Template Location

See: `docs/kb/context7-cache/ux-patterns/health-dashboard-dependencies-tab-pattern.md`

---

## 📚 Related Resources

- [Health Dashboard README](../services/health-dashboard/README.md)
- [Component Library](../services/health-dashboard/src/components/)
- [Architecture Docs](architecture/)
- [Context7 KB Cache](context7-cache/)

---

**Last Updated:** 2025-10-12  
**Maintained By:** BMAD Agents  
**Quick Access:** `docs/kb/ux-pattern-quick-reference.md`


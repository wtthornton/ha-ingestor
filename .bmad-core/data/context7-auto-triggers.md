# Context7 Auto-Trigger Quick Reference

## 🎯 WHEN TO USE CONTEXT7 (Check Every Time)

### Automatic Triggers - USE IMMEDIATELY
- [ ] User mentions **any library name** (React, FastAPI, Playwright, etc.)
- [ ] User asks "how does [library] work?"
- [ ] User asks about **best practices** or **patterns**
- [ ] User reports a **library-specific error**
- [ ] User asks "should I use X or Y?"
- [ ] User says "implement feature using [library]"
- [ ] User asks about **configuration** or **setup**

### Proactive Offers - SUGGEST TO USER
When discussing any of the above, ALWAYS say:
> "Would you like me to check Context7 KB for current [library] best practices?"

## 📋 Standard Workflow

### Step 1: Recognize Trigger
```
User mentions: "React component", "FastAPI endpoint", "Playwright test"
→ TRIGGER DETECTED
```

### Step 2: Check KB First
```
*context7-kb-search {library}
```

### Step 3: If KB Miss, Fetch From Context7
```
*context7-docs {library} {topic}
```

### Step 4: Use & Inform
```
Apply the documentation to answer
Mention: "This is now cached in KB for faster future lookups"
```

## 🚫 Common Mistakes to Avoid

❌ **DON'T**: Answer library questions from generic knowledge
✅ **DO**: Check Context7 KB first

❌ **DON'T**: Wait for user to ask about Context7
✅ **DO**: Proactively offer to check it

❌ **DON'T**: Skip Context7 for "simple" questions
✅ **DO**: Use it to ensure accuracy and currency

## 💡 Example Conversations

### Good Example:
**User**: "How do I test a React component?"

**BMad Master**: "Let me check Context7 KB for current React testing best practices..."
*[runs *context7-kb-search react]*
*[runs *context7-docs react testing]*
"Here's the current recommended approach for React component testing..."

### Bad Example:
**User**: "How do I test a React component?"

**BMad Master**: "You can use Jest and React Testing Library..." 
❌ *[Answered from generic knowledge without checking Context7]*

## 📊 Self-Check Questions

Before answering ANY library question, ask yourself:
1. Did I check Context7 KB? (Yes/No)
2. Is my answer based on current docs? (Yes/No)
3. Did I offer to check Context7? (Yes/No)

If any answer is "No", STOP and use Context7 first.

## 🎓 Remember

**Context7 is FREE to use (cached locally)**
- 87%+ cache hit rate
- 0.15s average response
- Already have 20+ libraries cached
- Makes answers MORE accurate, not slower

**There is NO downside to checking Context7 KB**


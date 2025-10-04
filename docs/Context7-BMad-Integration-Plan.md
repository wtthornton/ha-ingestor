# Context7 MCP Integration Plan for BMad Methodology

## Executive Summary

This document outlines a comprehensive plan to integrate Context7 MCP (Model Context Protocol) tools into the BMad methodology to enhance code and design creation while maintaining token efficiency. The integration focuses on strategic invocation points where Context7's library documentation capabilities can provide maximum value without bloating token usage.

## Current State Analysis

### BMad Structure
- **Agents**: 10 specialized agents (architect, dev, pm, qa, etc.) with specific roles
- **Workflows**: Planning phase (web) → Development phase (IDE)
- **Dependencies**: Tasks, templates, checklists, data files loaded on-demand
- **Token Management**: Lean context loading, resource sharing across agents

### Context7 MCP Capabilities
- **resolve-library-id**: Resolves package names to Context7-compatible library IDs
- **get-library-docs**: Fetches up-to-date documentation for libraries
- **Token Parameters**: Configurable token limits (default 5000)
- **Topic Focus**: Can focus documentation on specific topics (e.g., 'hooks', 'routing')

## Integration Strategy

### 1. Strategic Integration Points

#### A. Architecture Phase (Winston - Architect Agent)
**When**: Technology selection and API design decisions
**Context7 Usage**: 
- Resolve library IDs for proposed technology stacks
- Fetch documentation for architectural patterns and best practices
- Focus on topics like 'architecture', 'design-patterns', 'scalability'

**Token Efficiency**: 
- Only invoke when making technology decisions
- Use topic focus to limit documentation scope
- Cache resolved library IDs to avoid repeated resolution

#### B. Development Phase (James - Dev Agent)
**When**: Implementation of specific features requiring library knowledge
**Context7 Usage**:
- Resolve library IDs for dependencies mentioned in stories
- Fetch focused documentation for specific implementation tasks
- Focus on topics like 'hooks', 'routing', 'authentication', 'testing'

**Token Efficiency**:
- Only invoke when story explicitly mentions external libraries
- Use minimal token limits (2000-3000) for focused documentation
- Cache documentation for repeated library usage within same story

#### C. Quality Assurance Phase (Quinn - QA Agent)
**When**: Risk assessment and test design for library integrations
**Context7 Usage**:
- Resolve library IDs for libraries with known security/performance risks
- Fetch documentation on testing patterns and best practices
- Focus on topics like 'testing', 'security', 'performance'

**Token Efficiency**:
- Only invoke for high-risk stories involving external libraries
- Use topic focus to get only relevant testing/security documentation

### 2. Token-Efficient Implementation

#### A. Conditional Invocation Rules
```yaml
context7_invocation_rules:
  architect:
    - trigger: "technology_selection_required"
    - condition: "new_library_mentioned OR architecture_decision_needed"
    - token_limit: 4000
    - topics: ["architecture", "design-patterns", "scalability"]
  
  dev:
    - trigger: "implementation_with_external_library"
    - condition: "story_mentions_library AND implementation_task"
    - token_limit: 3000
    - topics: ["hooks", "routing", "authentication", "testing"]
  
  qa:
    - trigger: "high_risk_library_assessment"
    - condition: "risk_score >= 6 AND external_library_involved"
    - token_limit: 2500
    - topics: ["testing", "security", "performance"]
```

#### B. Caching Strategy
- **Library ID Cache**: Store resolved library IDs in session memory
- **Documentation Cache**: Cache frequently used documentation for 1 hour
- **Topic-Specific Cache**: Separate caches for different topics to avoid conflicts

#### C. Smart Token Management
- **Progressive Loading**: Start with minimal tokens, increase if needed
- **Topic Focus**: Always use topic parameter to limit scope
- **Selective Invocation**: Only invoke when value is clear and immediate

### 3. Implementation Plan

#### Phase 1: Core Integration (Week 1)
1. **Add Context7 Commands to BMad Master**
   - Add `*context7-resolve {library}` command
   - Add `*context7-docs {library} {topic}` command
   - Add `*context7-cache` command for cache management

2. **Update Agent Definitions**
   - Add Context7 capabilities to architect, dev, and qa agents
   - Include Context7 invocation rules in agent personas
   - Add Context7 dependency to relevant tasks

#### Phase 2: Workflow Integration (Week 2)
1. **Update Architecture Templates**
   - Add Context7 invocation points in technology selection sections
   - Include Context7 documentation in architectural decision rationale
   - Add Context7 usage guidelines to architecture templates

2. **Update Development Tasks**
   - Modify `develop-story` command to include Context7 checks
   - Add Context7 invocation for library-specific implementation tasks
   - Include Context7 documentation in development notes

3. **Update QA Tasks**
   - Add Context7 invocation to risk assessment tasks
   - Include Context7 documentation in test design tasks
   - Add Context7 usage to quality gate criteria

#### Phase 3: Optimization (Week 3)
1. **Token Usage Monitoring**
   - Implement token usage tracking for Context7 calls
   - Add token efficiency metrics to agent performance
   - Create token usage reports for optimization

2. **Cache Optimization**
   - Implement intelligent caching strategies
   - Add cache hit/miss metrics
   - Optimize cache invalidation policies

3. **Usage Analytics**
   - Track Context7 invocation patterns
   - Identify most valuable integration points
   - Optimize invocation rules based on usage data

### 4. Technical Implementation

#### A. BMad Master Agent Updates
```yaml
# Add to .bmad-core/agents/bmad-master.md
commands:
  - context7-resolve {library}: Resolve library name to Context7 ID
  - context7-docs {library} {topic}: Get focused documentation
  - context7-cache: Manage Context7 documentation cache
  - context7-stats: Show Context7 usage statistics
```

#### B. Agent-Specific Integration
```yaml
# Add to architect agent
context7_integration:
  enabled: true
  default_topics: ["architecture", "design-patterns", "scalability"]
  token_limit: 4000
  cache_duration: 3600

# Add to dev agent  
context7_integration:
  enabled: true
  default_topics: ["hooks", "routing", "authentication", "testing"]
  token_limit: 3000
  cache_duration: 1800

# Add to qa agent
context7_integration:
  enabled: true
  default_topics: ["testing", "security", "performance"]
  token_limit: 2500
  cache_duration: 1800
```

#### C. Task Integration Points
```yaml
# Add to relevant tasks
context7_triggers:
  - task: "create-doc.md"
    trigger: "technology_selection_section"
    action: "resolve_and_fetch_docs"
  
  - task: "develop-story.md"
    trigger: "library_implementation_task"
    action: "fetch_focused_docs"
  
  - task: "risk-profile.md"
    trigger: "external_library_risk"
    action: "fetch_security_docs"
```

### 5. Usage Guidelines

#### A. When to Use Context7
✅ **DO Use Context7 When**:
- Making technology selection decisions
- Implementing features with external libraries
- Assessing risks for library integrations
- Need up-to-date best practices
- Documentation is unclear or outdated

❌ **DON'T Use Context7 When**:
- Working with well-known, stable libraries
- Implementation is straightforward
- Token budget is limited
- Documentation is already available locally
- Library is project-specific or internal

#### B. Best Practices
1. **Always use topic focus** to limit documentation scope
2. **Start with minimal tokens** and increase if needed
3. **Cache resolved library IDs** to avoid repeated resolution
4. **Use Context7 documentation to supplement**, not replace, local knowledge
5. **Monitor token usage** and optimize invocation patterns

#### C. Token Management
- **Default Limits**: 2500-4000 tokens per invocation
- **Topic Focus**: Always specify relevant topics
- **Progressive Loading**: Start small, expand if needed
- **Cache Strategy**: Cache for 30-60 minutes based on usage patterns

### 6. Success Metrics

#### A. Quality Metrics
- **Documentation Accuracy**: Improved architectural decisions
- **Implementation Quality**: Fewer library integration issues
- **Risk Assessment**: Better identification of library-related risks
- **Development Speed**: Faster implementation of library features

#### B. Efficiency Metrics
- **Token Usage**: < 10% increase in total token usage
- **Cache Hit Rate**: > 70% for frequently used libraries
- **Invocation Frequency**: Optimal balance of usage vs. efficiency
- **Response Time**: < 2 seconds for Context7 calls

#### C. User Satisfaction
- **Agent Performance**: Improved quality of architectural and development decisions
- **Documentation Quality**: More accurate and up-to-date information
- **Development Experience**: Smoother library integration process

### 7. Risk Mitigation

#### A. Token Bloat Prevention
- **Strict Invocation Rules**: Only invoke when value is clear
- **Token Limits**: Enforce maximum token limits per invocation
- **Cache Strategy**: Aggressive caching to reduce repeated calls
- **Monitoring**: Real-time token usage tracking

#### B. Quality Assurance
- **Validation**: Verify Context7 documentation accuracy
- **Fallback**: Graceful degradation when Context7 is unavailable
- **Testing**: Comprehensive testing of Context7 integration
- **Monitoring**: Track Context7 service availability and performance

#### C. User Experience
- **Transparency**: Clear indication when Context7 is being used
- **Control**: User ability to disable Context7 integration
- **Feedback**: User feedback on Context7 usefulness
- **Documentation**: Clear guidelines on when and how to use Context7

### 8. Implementation Timeline

#### Week 1: Foundation
- [ ] Add Context7 commands to BMad Master
- [ ] Update agent definitions with Context7 capabilities
- [ ] Implement basic caching strategy
- [ ] Create Context7 invocation rules

#### Week 2: Integration
- [ ] Update architecture templates with Context7 integration
- [ ] Modify development tasks to include Context7 checks
- [ ] Update QA tasks with Context7 risk assessment
- [ ] Implement token usage monitoring

#### Week 3: Optimization
- [ ] Optimize caching strategies
- [ ] Fine-tune invocation rules based on usage
- [ ] Implement usage analytics
- [ ] Create user documentation and guidelines

#### Week 4: Testing & Validation
- [ ] Comprehensive testing of Context7 integration
- [ ] Performance testing and optimization
- [ ] User acceptance testing
- [ ] Documentation and training materials

### 9. Conclusion

This integration plan provides a comprehensive approach to incorporating Context7 MCP into the BMad methodology while maintaining token efficiency and enhancing code and design creation. The strategic integration points, token-efficient implementation, and comprehensive monitoring ensure that Context7 adds value without bloating the system.

The key to success is maintaining the balance between enhanced capabilities and token efficiency, ensuring that Context7 is used strategically rather than indiscriminately. With proper implementation, this integration will significantly improve the quality of architectural decisions, development implementations, and risk assessments while maintaining the lean, efficient nature of the BMad methodology.

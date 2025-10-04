# Context7 MCP Integration Guide

## Overview

Context7 MCP (Model Context Protocol) integration provides BMad with up-to-date library documentation capabilities, enhancing code and design creation without token bloat.

## Integration Architecture

### Components
- **Library Resolution**: `mcp_Context7_resolve-library-id` - Resolves library names to Context7-compatible IDs
- **Documentation Retrieval**: `mcp_Context7_get-library-docs` - Fetches focused documentation for libraries
- **Token Management**: Optimized token usage with topic focus and caching
- **Error Handling**: Graceful degradation when Context7 is unavailable

### Agent Integration
- **BMad Master**: Direct Context7 commands and task execution
- **Architect**: Context7 awareness for technology decisions
- **Dev**: Context7 awareness for library implementations
- **QA**: Context7 awareness for risk assessments

## Usage Patterns

### Direct Commands
```bash
# Resolve library name
*context7-resolve react

# Get documentation
*context7-docs react hooks

# Get help
*context7-help
```

### Agent Integration
- Agents automatically suggest Context7 when relevant
- Templates include Context7 usage instructions
- Workflows integrate Context7 for technology decisions

## Token Efficiency

### Optimization Strategies
- **Topic Focus**: Always specify relevant topics to limit scope
- **Token Limits**: Default 3000 tokens, configurable per agent
- **Caching**: Results cached to avoid repeated calls
- **Progressive Loading**: Start small, increase if needed

### Agent-Specific Limits
- **Architect**: 4000 tokens, topics: architecture, design-patterns, scalability
- **Dev**: 3000 tokens, topics: hooks, routing, authentication, testing
- **QA**: 2500 tokens, topics: testing, security, performance

## Error Handling

### Common Errors
- **Library Not Found**: Graceful fallback with error message
- **Context7 Unavailable**: Fallback to local knowledge
- **Invalid Topic**: Suggest valid topics
- **Token Limit Exceeded**: Suggest smaller topic scope

### Fallback Strategies
- Use local documentation when available
- Suggest alternative approaches
- Provide error context and recovery options

## Best Practices

### When to Use Context7
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

### Usage Guidelines
1. **Always use topic focus** to limit documentation scope
2. **Start with minimal tokens** and increase if needed
3. **Cache resolved library IDs** to avoid repeated resolution
4. **Use Context7 documentation to supplement**, not replace, local knowledge
5. **Monitor token usage** and optimize invocation patterns

## Implementation Levels

### Low Complexity (30 minutes)
- Agent awareness added to personas
- Template suggestions for Context7 usage
- No system changes or new commands
- Zero risk, easy rollback

### Medium Complexity (1-2 hours)
- Direct Context7 commands in BMad Master
- Simple task files for Context7 integration
- Basic error handling and workflows
- Low risk, user-controlled usage

### High Complexity (1-2 weeks)
- Automatic Context7 invocation based on context
- Advanced caching and token management
- Deep workflow integration
- Medium-high risk, seamless experience

### Very High Complexity (2-4 weeks)
- Machine learning for invocation decisions
- Advanced analytics and optimization
- Multi-agent coordination
- High risk, intelligent system

## Troubleshooting

### Common Issues
- **Context7 Commands Not Available**: Check BMad Master agent configuration
- **Library Resolution Fails**: Verify library name spelling and availability
- **Documentation Not Retrieved**: Check topic parameter and token limits
- **Performance Issues**: Monitor token usage and optimize caching

### Debug Steps
1. Test Context7 connectivity with `*context7-resolve test`
2. Check agent configuration and dependencies
3. Verify template integration points
4. Monitor token usage and performance
5. Review error logs and fallback behavior

## Future Enhancements

### Planned Features
- Advanced caching strategies
- Predictive documentation loading
- Cross-agent Context7 sharing
- Usage analytics and optimization
- Machine learning for invocation decisions

### Integration Opportunities
- IDE-specific Context7 integration
- CI/CD pipeline Context7 usage
- Documentation generation from Context7
- Automated library updates and migrations

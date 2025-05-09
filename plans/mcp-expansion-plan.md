# CodeKite MCP Expansion Plan

## Current Status

CodeKite, as a Code Intelligence Agent, currently exposes a limited subset of its capabilities through the Model Context Protocol (MCP). This document outlines the current coverage and identifies key areas for expansion to provide comprehensive access to all CodeKite features through the MCP interface.

## Currently Implemented MCP Components

### Tools

| Tool Name                  | Description                        | Source Module                  |
| -------------------------- | ---------------------------------- | ------------------------------ |
| `codekite_open_repository` | Opens a local or remote repository | repository.py                  |
| `codekite_search_code`     | Performs pattern-based code search | code_searcher.py               |
| `codekite_build_context`   | Generates basic context for LLMs   | context_extractor.py (limited) |

### Resources

| Resource URI                                 | Description               | Source Module                  |
| -------------------------------------------- | ------------------------- | ------------------------------ |
| `codekite://repository/{repo_id}/structure`  | Repository file structure | repository.py                  |
| `codekite://repository/{repo_id}/summary`    | Repository statistics     | repository.py                  |
| `codekite://repository/{repo_id}/docstrings` | Repository docstrings     | docstring_indexer.py (limited) |

## Missing MCP Implementations

The following CodeKit capabilities are not yet accessible through the MCP interface:

### 1. Dependency Analysis (dependency_analyzer.py)

**Missing Capabilities:**

- Cross-file dependency tracking
- Impact analysis for code changes
- Dependency graph generation
- Import/usage relationship mapping

**Implementation Plan:**

- Create `codekite_analyze_dependencies` tool to generate dependency maps
- Add `codekite://repository/{repo_id}/dependencies` resource for dependency graph access
- Implement `codekite_analyze_impact` tool to predict the impact of code changes

### 2. Vector Search (vector_searcher.py)

**Missing Capabilities:**

- Semantic code search
- Embeddings-based similarity matching
- Multi-language semantic understanding
- Vector search configuration

**Implementation Plan:**

- Create `codekite_semantic_search` tool for embeddings-based searches
- Add `codekite://repository/{repo_id}/embeddings` resource for vector representation access
- Implement `codekite_configure_vector_search` tool for search customization

### 3. Code Summarization (summaries.py)

**Missing Capabilities:**

- LLM-based code summarization
- File, class, and function summarization
- Configurable summary generation
- Multi-model support (OpenAI, Anthropic, Google)

**Implementation Plan:**

- Create `codekite_summarize_file` tool for file-level summaries
- Create `codekite_summarize_symbol` tool for class/function summaries
- Add `codekite://repository/{repo_id}/summaries` resource for cached summary access
- Implement `codekite_configure_summaries` tool for LLM configuration

### 4. Repository Mapping (repo_mapper.py)

**Missing Capabilities:**

- Comprehensive repository mapping
- Code structure analysis
- Entity-relationship mapping
- Code navigation graph

**Implementation Plan:**

- Create `codekite_map_repository` tool for comprehensive mapping
- Add `codekite://repository/{repo_id}/map` resource for map access
- Implement `codekite_get_symbol_locations` tool for symbol location lookup

### 5. Docstring Indexing (docstring_indexer.py)

**Missing Capabilities:**

- Full docstring indexing
- Docstring search
- Documentation coverage analysis
- Documentation quality assessment

**Implementation Plan:**

- Create `codekite_index_docstrings` tool to trigger indexing
- Enhance existing `codekite://repository/{repo_id}/docstrings` resource
- Add `codekite_search_docstrings` tool for specialized docstring search
- Implement `codekite_analyze_documentation` tool for coverage analysis

### 6. Advanced Context Assembly (context_extractor.py, llm_context.py)

**Missing Capabilities:**

- Customizable context templates
- Context tailoring for different LLMs
- Token optimization strategies
- Context quality metrics

**Implementation Plan:**

- Enhance existing `codekite_build_context` tool with more parameters
- Add `codekite://repository/{repo_id}/context_templates` resource
- Create `codekite_optimize_context` tool for token usage optimization
- Implement `codekite_configure_context` tool for template management

## Implementation Priorities

### Phase 1: High-Value Capabilities

1. **Code Summarization**
   - Immediate value for AI assistants
   - Relatively straightforward implementation
   - High demand from users

2. **Semantic Search**
   - Significant enhancement over current search
   - Enables natural language code queries
   - Well-defined API boundaries

### Phase 2: Advanced Analysis

1. **Advanced Context Assembly**
   - Builds on existing context functionality
   - Critical for optimal LLM integration
   - Improves token efficiency

2. **Dependency Analysis**
   - Provides critical structural understanding
   - Enables impact analysis workflows
   - Foundation for many advanced features

### Phase 3: Complete Coverage

1. **Repository Mapping**
   - Comprehensive codebase understanding
   - Foundation for visualization tools
   - Advanced navigation capabilities

2. **Docstring Indexing**
   - Documentation quality improvements
   - Knowledge graph integration
   - Developer assistance features

## Conclusion

Expanding CodeKit's MCP interface to cover all major capabilities will significantly enhance its utility for AI assistants and other tools. The phased approach outlined in this document allows for incremental delivery of value while maintaining a clear path toward complete coverage.

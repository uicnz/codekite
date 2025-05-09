# Tech Context: CodeKit

## Technologies Used

### Core Technologies

- **Python**: Primary implementation language
- **Tree-sitter**: Language parsing library for code analysis
- **uv**: Modern Python packaging and environment management
- **Vector Database**: For semantic code search capabilities
- **Language Grammars**: Tree-sitter grammars for supported languages
- **FastMCP**: MCP server framework for AI assistant integration

### Supported Languages

- Python
- JavaScript/TypeScript
- Go
- Rust
- Ruby
- Java
- C
- HCL (HashiCorp Configuration Language)

## Development Setup

### Environment Management

- **uv**: Native-only approach for Python environment management
- **pyproject.toml**: Modern Python project configuration

### Building & Testing

- **Makefile**: Automation for common tasks
- **pytest**: Test framework for Python code
- **scripts/**: Utility scripts for development workflow
  - `benchmark.py`: Performance testing
  - `index.py`: Indexing utilities
  - `release.sh`: Release automation
  - `test.sh`: Testing automation
  - `typecheck.sh`: Type checking

### Documentation

- **Astro**: Static site generator for documentation
- **MDX**: Markdown with JSX for interactive documentation
- **Custom Components**: Specialized documentation components

## Technical Constraints

### Performance Requirements

- Must handle repositories with 100,000+ lines of code efficiently
- Search operations should return results within reasonable time frames (seconds not minutes)
- Memory usage must scale reasonably with repository size
- MCP server must respond quickly to client requests

### Compatibility

- Python 3.8+ required
- No emoji usage anywhere in the codebase
- Must follow strict markdown linting rules including blank lines after headings
- MCP server must support multiple transport protocols

### Development Standards

- All code must be typed with proper annotations
- Tests required for all functionality
- Documentation required for all public APIs
- Shell scripts must pass shellcheck validation
- Status indicators must use `[PASS]` and `[FAIL]` text format (not emojis)

## Dependencies

### Direct Dependencies

- **tree-sitter**: Core dependency for code parsing
- **tree-sitter-languages**: Language-specific grammars
- **numpy/scipy**: For vector operations in semantic search
- **faiss** (or similar): Vector similarity search
- **pydantic**: Data validation and settings management
- **fastapi**: Web framework for REST API
- **uvicorn**: ASGI server for FastAPI
- **fastmcp**: MCP server framework
- **pytest**: Testing framework
- **typing-extensions**: Enhanced typing capabilities
- **asyncio**: Asynchronous I/O for MCP server

### External Resources

- **Version Control Systems**: Git support as primary focus
- **Documentation System**: Astro-based documentation
- **CI/CD**: Testing and deployment pipelines
- **MCP Protocol**: Standard protocol for AI tool and context access

## Implementation Details

### Module Structure

- **repository.py**: Core repository interface
- **code_searcher.py**: Code search implementations
- **docstring_indexer.py**: Docstring extraction and indexing
- **summaries.py**: Code summarization logic
- **tree_sitter_symbol_extractor.py**: Symbol extraction using tree-sitter
- **vector_searcher.py**: Semantic search functionality
- **context_extractor.py**: Context extraction logic
- **dependency_analyzer.py**: Dependency analysis
- **llm_context.py**: LLM context assembly utilities
- **repo_mapper.py**: Repository mapping functionality
- **cli.py**: Command-line interface
- **mcp/**: MCP server implementation
  - **api_client.py**: Client wrapper for MCP tools
  - **server.py**: MCP server implementation

### MCP Integration

- **Transport Protocols**: Support for Streamable HTTP, SSE, and STDIO
- **Tools**: Repository opening (`codekite_open_repository`), code search (`codekite_search_code`), context building (`codekite_build_context`)
- **Resources**: Repository structure (`codekite://repository/{id}/structure`), summary (`codekite://repository/{id}/summary`), docstrings (`codekite://repository/{id}/docstrings`)
- **Asynchronous Operations**: All MCP operations are async for better performance
- **JSON Schema Generation**: Automatic from Python type annotations
- **Parameter Validation**: Input validation for all exposed tools
- **Response Serialization**: Consistent formatting for client consumption
- **Lazy Loading**: Module initialization uses lazy loading to avoid circular imports
- **Function Namespacing**: All MCP functions use `codekite_` prefix for compatibility with other MCP servers

### Data Storage

- In-memory data structures for small projects
- Disk-based storage for larger projects
- Vector database for semantic search embeddings
- Repository mapping for structure and relationships
- In-memory repository storage for MCP server

## Technical Roadmap Considerations

### Current Technical Focus

- Improving performance for large repositories
- Enhancing semantic search capabilities
- Adding support for more languages
- Refining the context assembly process
- Extending MCP tool and resource offerings

### Technical Debt Areas

- Performance optimization for very large codebases
- Edge case handling in multilingual contexts
- Comprehensive integration testing
- MCP client implementation improvements

### Infrastructure Needs

- Benchmarking system for performance tracking
- Improved documentation deployment
- Testing across various repository sizes and types
- MCP client libraries for different languages

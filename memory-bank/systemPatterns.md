# System Patterns: CodeKit

## System Architecture

CodeKit follows a modular architecture where components are loosely coupled but highly cohesive. The design emphasizes flexibility, extensibility, and interoperability between components.

## Key Components

### Repository Interface

The foundation of the system that provides access to code repositories and their contents. It abstracts away the details of fetching, parsing, and managing code files.

- **Responsibilities**: Repository access, file management, repository indexing
- **Dependencies**: External version control systems
- **Consumers**: All other components

### Code Analysis Engine

Core analysis infrastructure that processes code syntax and semantics across multiple languages.

- **Responsibilities**: Parsing code, extracting symbols, determining relationships
- **Dependencies**: Tree-sitter, language-specific parsers
- **Consumers**: Searcher, Summarizer, Dependency Analyzer

### Indexing System

Responsible for extracting and indexing various types of information from codebases.

- **Responsibilities**: Docstring extraction, code structure indexing
- **Dependencies**: Repository Interface, Code Analysis Engine
- **Consumers**: Search components, Context Extractor

### Search Components

Collection of search mechanisms catering to different search approaches.

- **Types**: Semantic search, symbol search, docstring search
- **Dependencies**: Indexing System, Repository Interface
- **Consumers**: Context Assembler, Client API

### Summarization Engine

Generates concise summaries of code components at various granularities.

- **Responsibilities**: Code understanding, abstraction, summarization
- **Dependencies**: Code Analysis Engine, Repository Interface
- **Consumers**: Context Assembler, Client API

### Context Assembly

Intelligently assembles relevant code context based on specific queries or needs.

- **Responsibilities**: Context selection, formatting, organization
- **Dependencies**: Search Components, Summarization Engine, Dependency Analyzer
- **Consumers**: Client API

### MCP Server

Model Context Protocol server that provides AI assistants with standardized access to CodeKit's capabilities.

- **Responsibilities**: Exposing tools and resources, handling client requests
- **Dependencies**: Repository Interface, Search Components, Context Assembly
- **Consumers**: AI assistants and other MCP clients
- **Components**:
  - **Tools**: Repository operations, code search, context building
  - **Resources**: Repository structure, summary information, documentation

## Design Patterns Used

### Factory Pattern

Used for creating appropriate language-specific parsers and analyzers.

```python
# Conceptual example
class LanguageParserFactory:
    @staticmethod
    def create_parser(language):
        if language == "python":
            return PythonParser()
        elif language == "javascript":
            return JavaScriptParser()
        # etc.
```

### Strategy Pattern

Employed for different search strategies that can be selected at runtime.

```python
# Conceptual example
class SearchContext:
    def __init__(self, strategy):
        self._strategy = strategy

    def search(self, query, repository):
        return self._strategy.search(query, repository)
```

### Observer Pattern

Used for notifying components about changes in the repository.

```python
# Conceptual example
class RepositorySubject:
    def __init__(self):
        self._observers = []

    def notify(self, event):
        for observer in self._observers:
            observer.update(event)
```

### Repository Pattern

Core pattern for abstracting data access and manipulation.

### Adapter Pattern

Used to provide consistent interfaces across different version control systems.

### Facade Pattern

Used in the MCP server to simplify access to the complex underlying system:

```python
# Conceptual example
@mcp.tool()
async def search_code(repo_id: str, query: str, file_pattern: str = "*.py"):
    """Search for code matching a pattern."""
    # This provides a simple interface to the complex search subsystem
    repo = repository_store.get(repo_id)
    return repo.search_text(query, file_pattern=file_pattern)
```

## Component Relationships

```sh
Repository Interface
     ↑  ↑  ↑
     |  |  |
     |  |  +----------------+
     |  |                   |
     |  +--------+          |
     |           |          |
Code Analysis    |          |
  Engine         |          |
     ↑           |          |
     |           |          |
     +-----+     |          |
           |     |          |
     +-----+-----+-----+    |
     |     |     |     |    |
     ↓     ↓     ↓     ↓    ↓
Indexing  Search  Summary  Dependency
 System    Comp.  Engine   Analyzer
     ↑      ↑       ↑        ↑
     |      |       |        |
     +------+-------+--------+
            |
            ↓
    Context Assembler
            ↑
            |
            ↓
     +------+------+
     |             |
     ↓             ↓
 REST API      MCP Server
 (FastAPI)     (FastMCP)
```

## Data Flow

1. **Repository Initialization**: Client initializes repository
2. **Indexing**: System indexes code, docstrings, and symbols
3. **Query Processing**: Client queries are translated to appropriate search strategies
4. **Context Assembly**: Relevant code, summaries, and relationship data are assembled
5. **Response Delivery**: Formatted context is returned to the client

## MCP Integration Architecture

MCP Server provides two main types of interactions:

### Tools

Executable capabilities exposed to AI assistants:

- `codekite_open_repository`: Open and initialize a repository
- `codekite_search_code`: Find code matching a pattern or query
- `codekite_build_context`: Generate LLM-ready context for code understanding

### Resources

Data sources that provide information to AI assistants:

- `codekite://repository/{id}/structure`: Hierarchical repository structure
- `codekite://repository/{id}/summary`: Repository statistics and metadata
- `codekite://repository/{id}/docstrings`: Documentation from the codebase

### MCP Protocol Handling

1. **Client Connection**: Client connects to MCP server using a supported transport
2. **Authentication**: (When configured) Client authenticates via OAuth
3. **Tool Discovery**: Client lists available tools and resources
4. **Tool Invocation**: Client sends a request to execute a tool
5. **Parameter Validation**: Server validates parameters against schema
6. **Tool Execution**: Server executes the tool with validated parameters
7. **Response Serialization**: Result is serialized to appropriate MCP format
8. **Response Delivery**: Result is sent back to client

## Technical Decisions

### Tree-sitter for Code Parsing

Decision to use Tree-sitter for code parsing provides language-agnostic parsing capabilities with high performance and accuracy.

### Vector-based Semantic Search

Using vector embeddings for semantic code search enables understanding of code intent beyond textual similarity.

### Modular Design Philosophy

Designing components with clear boundaries and interfaces allows for:

- Replacing implementation details without affecting the whole system
- Using components independently or in combination
- Adding support for new languages incrementally
- Extending search or summarization capabilities without refactoring

### FastMCP for MCP Server

Using FastMCP provides:

- Support for multiple transport protocols (Streamable HTTP, SSE, STDIO)
- Automatic schema generation from Python type annotations
- Built-in parameter validation
- Context injection for progress reporting and logging

## Cross-Cutting Concerns

### Error Handling

Consistent error handling approach across components:

- Specific exception types for different failure modes
- Graceful degradation when specific features fail
- Clear error messages for debugging

### Performance Considerations

- Lazy loading of components when possible
- Caching of parsed code and intermediate results
- Parallelization of independent operations
- Configurable trade-offs between performance and accuracy

### Extensibility Points

- Language support extension via Tree-sitter grammar plugins
- Custom search strategy implementation
- Summary generation customization
- Repository adapter extension
- MCP tool and resource extension

### Authentication & Security

- OAuth support for MCP server (when configured)
- Input validation for all exposed endpoints
- Safe handling of repository access

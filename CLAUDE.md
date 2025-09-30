# CodeKite Project Instructions

## Project Overview

CodeKite is a Python toolkit for codebase mapping, symbol extraction, code search, and context generation for LLMs. It provides a structured API for analyzing codebases and generating appropriate context for various development tasks.

## Core Architecture

### Primary Components

- **Repository** - Main interface for accessing codebases (local or remote GitHub repos)
- **RepoMapper** - Maps repository structure and extracts symbols using tree-sitter
- **TreeSitterSymbolExtractor** - Language-aware symbol extraction for 9+ languages
- **CodeSearcher** - Text and regex search across files
- **ContextExtractor** - Extracts context around specific lines or symbols
- **VectorSearcher** - Semantic search using vector embeddings
- **DocstringIndexer** - Builds searchable index of code summaries
- **Summarizer** - Generates natural language summaries using LLMs (OpenAI/Anthropic/Google)
- **DependencyAnalyzer** - Analyzes module dependencies and relationships
- **ContextAssembler** - Formats code context for LLM prompts

## Technology Stack

### Core Dependencies

- **Python 3.10+** - Primary implementation language
- **tree-sitter-language-pack** - Language parsing for code analysis
- **uv** - Package and environment management (ONLY tool allowed)
- **FastAPI + uvicorn** - API server
- **Typer** - CLI interface
- **chromadb + sentence-transformers** - Vector search capabilities
- **numpy** - Vector operations

### LLM Integrations

- **openai** - OpenAI API for summarization
- **anthropic** - Anthropic API for summarization
- **google-genai** - Google Gemini API for summarization
- **tiktoken** - Token counting for OpenAI models

### Development Tools

- **pytest** - Testing framework
- **mypy** - Type checking
- **ruff** - Linting
- **black** - Code formatting

### Supported Languages

Python, JavaScript, TypeScript, Go, Rust, Ruby, Java, C, HCL/Terraform

## Development Standards

### Absolute Rules

1. **NO EMOJIS EVER** - Use plain text: COMPLETED, ERROR, WARNING, SUCCESS
2. **uv ONLY** - Never use pip, poetry, or other package managers
3. **Type hints required** - All functions must have proper type annotations
4. **Tests required** - All functionality must have corresponding tests
5. **No market speak** - All documentation must be technical and direct

### Markdown Formatting

- Blank line after every heading
- Four backticks for nested Markdown code blocks
- Single trailing newline at end of files
- Never use bold/italic as pseudo-headers - use proper heading hierarchy
- No duplicate headings - make them unique with context
- Proper heading hierarchy - no skipping levels (# to ### invalid)
- No multiple consecutive blank lines
- Always enclose lists with blank lines above and below

### Code Quality

- Follow existing patterns in the codebase
- Maintain separation of concerns between components
- Lazy loading of components when possible
- Graceful degradation when features fail
- Clear error messages for debugging

## Build and Test Workflow

### Pre-commit Checklist

```bash
# Type checking
mypy src/codekite

# Run tests
pytest tests/ -v

# Or use the test script
bash scripts/test.sh -v
```

### CI/CD Pipeline

The project uses GitHub Actions (`.github/workflows/ci.yml`):

1. Python 3.13 setup
2. Install uv
3. Create venv and install dependencies with `uv pip install -e .[dev,all]`
4. Run mypy type checking on `src/codekite`
5. Execute test suite via `scripts/test.sh -v`

### Installation Methods

```bash
# Basic installation
uv tool install codekite

# With OpenAI support
uv tool install codekite[openai]

# With all features
uv tool install codekite[all]

# From source
git clone https://github.com/shaneholloman/codekite.git
cd codekite
uv sync
uv pip install -e .
```

## File Structure

```tree
/src/codekite/
  __init__.py                        # Package initialization
  repository.py                      # Main Repository interface
  repo_mapper.py                     # Repository mapping functionality
  tree_sitter_symbol_extractor.py    # Symbol extraction using tree-sitter
  code_searcher.py                   # Text search implementations
  context_extractor.py               # Context extraction logic
  vector_searcher.py                 # Semantic search functionality
  docstring_indexer.py               # Docstring extraction and indexing
  summaries.py                       # Code summarization logic
  dependency_analyzer.py             # Dependency analysis
  llm_context.py                     # LLM context assembly utilities
  cli.py                             # Command-line interface
  /api/
    app.py                           # FastAPI server implementation

/tests/                              # Test suite
/examples/                           # Usage examples
/scripts/                            # Development automation scripts
/memory-bank/                        # Project documentation and context
/docs/                               # Astro-based documentation site
```

## Common Development Tasks

### Adding New Language Support

1. Ensure tree-sitter grammar is available in `tree-sitter-language-pack`
2. Add language configuration to `TreeSitterSymbolExtractor`
3. Add test cases in `tests/test_symbol_extraction_multilang.py`
4. Update supported languages list in README.md

### Modifying Symbol Extraction

1. Update logic in `tree_sitter_symbol_extractor.py`
2. Run golden tests: `pytest tests/test_golden_symbols.py`
3. Update test fixtures if behavior intentionally changes
4. Verify across multiple languages

### Working with LLM Summarization

1. Configuration objects: `OpenAIConfig`, `AnthropicConfig`, `GoogleConfig`
2. Lazy import pattern to avoid mandatory dependencies
3. Environment variable support for API keys
4. Factory method pattern via `repo.get_summarizer(config)`

### CLI Development

- CLI is built with Typer in `cli.py`
- Entry point defined in `pyproject.toml` as `codekite = "codekite.cli:app"`
- Current commands: `version`, `search`, `serve`

## API Design Patterns

### Factory Pattern

Used for creating language parsers and component initialization:

```python
# Get summarizer with specific config
summarizer = repo.get_summarizer(config=openai_config)

# Get dependency analyzer
analyzer = repo.get_dependency_analyzer()

# Get context assembler
assembler = repo.get_context_assembler()
```

### Strategy Pattern

Different search strategies selectable at runtime:

- Text search (`search_text`)
- Semantic search (`search_semantic`)
- Symbol search (`extract_symbols`)

### Repository Pattern

Core abstraction for data access across components.

## Performance Considerations

- Must handle repositories with 100,000+ lines of code efficiently
- Search operations should complete in seconds, not minutes
- Memory usage must scale reasonably with repository size
- Caching of parsed code and intermediate results
- Parallelization of independent operations where possible

## Testing Philosophy

- Test real functionality, not mocks
- Understand code before writing tests
- Never modify production code without explicit permission
- Keep documentation concise
- Tests can be validators (prove features work) OR guardrails (prevent regressions)

## Known Technical Debt

- Performance optimization for very large codebases
- Edge case handling in multilingual contexts
- Comprehensive integration testing across repository sizes

## CLI Usage Examples

```bash
# Show version
codekite version

# Perform text search
codekite search /path/to/repo "search_query" --pattern "*.py"

# Start API server
codekite serve --port 8000
```

## Important Notes

1. Always prefer editing existing files over creating new ones
2. Never proactively create documentation files unless explicitly requested
3. Read files completely - never use offset/limit parameters
4. Follow the existing codebase patterns for consistency
5. Remote repository support via GitHub URL cloning to cache directory
6. Vector search requires embedding function on first use
7. LLM summarization requires installing extras: `codekite[openai]`, `codekite[anthropic]`, or `codekite[google]`

## Memory Bank Structure

The `/memory-bank/` directory contains:

- `projectBrief.md` - Project overview and goals
- `systemPatterns.md` - Architecture and design patterns
- `techContext.md` - Technologies and implementation details
- `productContext.md` - Product-level context
- `progress.md` - Development progress tracking
- `activeContext.md` - Current development focus

These files provide comprehensive context for AI-assisted development.

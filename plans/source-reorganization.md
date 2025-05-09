# CodeKite Source Code Reorganization Plan

## Current Structure

Currently, the CodeKite (Code Intelligence Agent) source code is organized with all core implementation files directly in the `src/codekite/` directory:

```tree
src/codekite/
├── __init__.py
├── api/
│   ├── __init__.py
│   └── app.py
├── cli.py
├── code_searcher.py
├── context_extractor.py
├── dependency_analyzer.py
├── docstring_indexer.py
├── llm_context.py
├── mcp/
│   ├── __init__.py
│   ├── api_client.py
│   └── server.py
├── repo_mapper.py
├── repository.py
├── summaries.py
├── tree_sitter_symbol_extractor.py
└── vector_searcher.py
```

As the codebase has grown, keeping all tool implementations in the top-level directory has made it increasingly difficult to maintain a clean separation of concerns. In particular, the following files implement core tool functionality and should be grouped together:

- code_searcher.py
- context_extractor.py
- dependency_analyzer.py
- docstring_indexer.py
- llm_context.py
- repo_mapper.py
- repository.py
- summaries.py
- tree_sitter_symbol_extractor.py
- vector_searcher.py

## Proposed Structure

The proposed reorganization creates a dedicated `tools` subdirectory to house all the tool implementation files:

```tree
src/codekite/
├── __init__.py
├── api/
│   ├── __init__.py
│   └── app.py
├── cli.py
├── mcp/
│   ├── __init__.py
│   ├── api_client.py
│   └── server.py
└── tools/
    ├── __init__.py
    ├── code_searcher.py
    ├── context_extractor.py
    ├── dependency_analyzer.py
    ├── docstring_indexer.py
    ├── llm_context.py
    ├── repo_mapper.py
    ├── repository.py
    ├── summaries.py
    ├── tree_sitter_symbol_extractor.py
    └── vector_searcher.py
```

## Migration Plan

### 1. Create the New Directory Structure

```bash
mkdir -p src/codekite/tools
touch src/codekite/tools/__init__.py
```

### 2. Implement Import Forwarding in the Tools Module

To maintain backward compatibility, we need to ensure that imports from the old locations continue to work. We'll do this by adding import forwarding in the `tools/__init__.py` file:

```python
# src/codekite/tools/__init__.py

# Re-export all tool classes and functions for backward compatibility
from .code_searcher import CodeSearcher
from .context_extractor import ContextExtractor
from .dependency_analyzer import DependencyAnalyzer
from .docstring_indexer import DocstringIndexer
from .llm_context import LLMContext
from .repo_mapper import RepoMapper
from .repository import Repository
from .summaries import Summarizer
from .tree_sitter_symbol_extractor import SymbolExtractor
from .vector_searcher import VectorSearcher

# Add any other exports needed
```

### 3. Implement Import Forwarding in the Main Module

Update the main `src/codekite/__init__.py` file to forward imports from the new locations:

```python
# src/codekite/__init__.py

# Import from new locations but expose at the top level for backward compatibility
from .tools.code_searcher import CodeSearcher
from .tools.context_extractor import ContextExtractor
from .tools.dependency_analyzer import DependencyAnalyzer
from .tools.docstring_indexer import DocstringIndexer
from .tools.llm_context import LLMContext
from .tools.repo_mapper import RepoMapper
from .tools.repository import Repository
from .tools.summaries import Summarizer
from .tools.tree_sitter_symbol_extractor import SymbolExtractor
from .tools.vector_searcher import VectorSearcher

# Add any other exports needed
```

### 4. Move Files to the New Location

```bash
# Move each file to the tools directory
mv src/codekite/code_searcher.py src/codekite/tools/
mv src/codekite/context_extractor.py src/codekite/tools/
mv src/codekite/dependency_analyzer.py src/codekite/tools/
mv src/codekite/docstring_indexer.py src/codekite/tools/
mv src/codekite/llm_context.py src/codekite/tools/
mv src/codekite/repo_mapper.py src/codekite/tools/
mv src/codekite/repository.py src/codekite/tools/
mv src/codekite/summaries.py src/codekite/tools/
mv src/codekite/tree_sitter_symbol_extractor.py src/codekite/tools/
mv src/codekite/vector_searcher.py src/codekite/tools/
```

### 5. Update Inter-Module Imports

Fix imports in all moved files to reference the new module structure:

```python
# Update imports like:
from codekite.repository import Repository
# to:
from codekite.tools.repository import Repository

# or for sibling imports:
from .repository import Repository
```

This requires a thorough audit of all import statements in the moved files.

### 6. Update MCP Server Imports

Update imports in the MCP server implementation to reference the new tool locations:

```python
# Update imports in src/codekite/mcp/server.py to reference tools
from ..tools.repository import Repository
from ..tools.code_searcher import CodeSearcher
# etc.
```

### 7. Update Tests

Update import paths in all test files to reference the new locations:

```python
# Change imports like:
from codekite.repository import Repository
# to:
from codekite.tools.repository import Repository
```

## Impact Analysis

### Code That Needs to Be Updated

1. **Direct imports**: Any code directly importing from the moved files
2. **Tests**: All tests referencing the moved files
3. **MCP server**: References to the moved files
4. **CLI implementation**: Any imports in cli.py
5. **API implementation**: Any imports in the api/ package

### Backward Compatibility

The import forwarding approach will maintain backward compatibility for code that imports directly from the `codekite` package. However, relative imports within the moved files will need to be updated.

### Performance Impact

There should be no measurable performance impact from this reorganization, as it only affects import paths, not runtime behavior.

## Testing Strategy

### Pre-Migration Tests

1. Run the full test suite to ensure all tests pass before migration
2. Generate a coverage report to ensure adequate test coverage

### Post-Migration Tests

1. Run the full test suite again to verify no regressions were introduced
2. Manually verify that example scripts still work
3. Test the MCP server to ensure it can still access all functionality

### Import Verification

Use a static analysis tool to verify all imports are correct:

```bash
# Use a tool like isort to check import order and validity
uv run isort --check-only src/
```

## Implementation Timeline

The reorganization should be done in a single, atomic commit to avoid inconsistent states. The entire process is expected to take approximately 2-3 hours, including testing.

## Rollback Plan

If issues arise, the rollback process is:

1. Revert the commit that moved the files
2. Remove any newly created directories
3. Run the test suite to verify the rollback was successful

## Future Considerations

After this reorganization, consider:

1. Further submodules based on functionality (e.g., `tools/search/`, `tools/analysis/`)
2. Documentation updates to reflect the new structure
3. Revisiting the public API to ensure a clean interface

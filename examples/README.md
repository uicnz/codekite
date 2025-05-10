# CodeKite Examples

This directory contains example scripts that demonstrate the capabilities of the CodeKite (Code Intelligence).

## Available Examples

### MCP Integration Examples

- **analyze_repo.py**: Uses the Model Context Protocol (MCP) client to analyze any GitHub repository, providing detailed structure, code patterns, and contextual understanding.

  ```sh
  # First, start the MCP server in a separate terminal:
  uv run python -m src.codekite.mcp.server

  # Then run the analyzer with a GitHub repository URL:
  python examples/analyze_repo.py https://github.com/username/repo

  # Search for specific patterns with custom results limit:
  python examples/analyze_repo.py https://github.com/username/repo --search "class" --max-results 10

  # Search for function definitions:
  python examples/analyze_repo.py https://github.com/username/repo --search "def\\s+\\w+" --max-results 15
  ```

- **clone_and_analyze.py**: Temporarily clones a repository locally, performs comprehensive analysis using the MCP server, then cleans up afterwards.

  ```sh
  # First, start the MCP server in a separate terminal:
  uv run python -m src.codekite.mcp.server

  # Then clone and analyze a repository:
  python examples/clone_and_analyze.py https://github.com/username/repo
  ```

### Core Functionality Examples

- **example_kit_capabilities.py**: Demonstrates the five core capabilities of CodeKite: code structure analysis, intelligent search, context extraction, LLM integration, and dependency analysis.

  ```sh
  uv run examples/example_kit_capabilities.py
  ```

- **example_repo_mapping.py**: Generates a complete JSON map of a repository's structure and symbols, useful for further analysis or visualization.

  ```sh
  # For local repository
  uv run examples/example_repo_mapping.py .

  # For remote GitHub repository
  uv run examples/example_repo_mapping.py https://github.com/username/repo
  ```

### Search Examples

- **example_semantic_search.py**: Demonstrates semantic code search using embeddings to find code based on natural language queries.

  ```sh
  uv run  examples/example_semantic_search.py --repo . --query "extract\_symbols"
  ```

### LLM Integration Examples

- **example_llm_summarization.py**: Shows how codekite can use LLMs like OpenAI's models to generate summaries of files, functions, and classes.

  ```sh
  # Requires an OpenAI API key
  export OPENAI_API_KEY='your-api-key'
  uv run examples/example_llm_summarization.py
  ```

### Remote Repository Examples

- **example_remote_repo.py**: Tests codekite's ability to clone and analyze remote GitHub repositories, demonstrating its remote capabilities.

  ```sh
  uv run examples/example_remote_repo.py https://github.com/shanholloman/codemapper
  uv run examples/example_remote_repo.py .
  ```

## Usage Notes

- All examples can be run from the root directory of the repository.
- Some examples require additional dependencies or API keys as noted above.
- Output files (like JSON maps) will be created in the current working directory.

## Running the MCP Server

The Model Context Protocol (MCP) server is a key component for the new analysis examples. It provides a standardized interface for AI assistants and other tools to access CodeKite's capabilities.

### Server Setup

```sh
# Start the server on the default port (8000)
uv run python -m src.codekite.mcp.server

# The server will output:
# [INFO] Starting Simple CodeKite MCP server...
# INFO:     Started server process [...]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### MCP Tools and Resources

The server exposes the following capabilities:

- Tools:
  - `codekite_open_repository`: Opens a local or remote repository
  - `codekite_search_code`: Searches for code patterns
  - `codekite_build_context`: Generates context for AI understanding

- Resources:
  - `codekite://repository/{id}/structure`: Repository structure
  - `codekite://repository/{id}/summary`: Repository statistics
  - `codekite://repository/{id}/docstrings`: Extracted docstrings

### Example MCP Workflow

1. Start the MCP server (`uv run python -m src.codekite.mcp.server`)
2. Run one of the analysis scripts, such as `analyze_repo.py`
3. The script connects to the server, opens a repository, and retrieves information
4. Results are displayed in a structured format

For detailed implementations, see the source code of the example scripts.

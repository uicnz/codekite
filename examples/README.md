# Kit Examples

This directory contains example scripts that demonstrate the capabilities of the Kit (Code Intelligence Toolkit).

## Available Examples

### Core Functionality Examples

- **example_kit_capabilities.py**: Demonstrates the five core capabilities of Kit: code structure analysis, intelligent search, context extraction, LLM integration, and dependency analysis.

  ```sh
  python examples/example_kit_capabilities.py
  ```

- **example_repo_mapping.py**: Generates a complete JSON map of a repository's structure and symbols, useful for further analysis or visualization.

  ```sh
  # For local repository
  python examples/example_repo_mapping.py .

  # For remote GitHub repository
  python examples/example_repo_mapping.py https://github.com/username/repo
  ```

### Search Examples

- **example_semantic_search.py**: Demonstrates semantic code search using embeddings to find code based on natural language queries.

  ```sh
  python examples/example_semantic_search.py "your search query"
  ```

### LLM Integration Examples

- **example_llm_summarization.py**: Shows how Kit can use LLMs like OpenAI's models to generate summaries of files, functions, and classes.

  ```sh
  # Requires an OpenAI API key
  export OPENAI_API_KEY='your-api-key'
  python examples/example_llm_summarization.py
  ```

### Remote Repository Examples

- **example_remote_repo.py**: Tests Kit's ability to clone and analyze remote GitHub repositories, demonstrating its remote capabilities.

  ```sh
  python examples/example_remote_repo.py https://github.com/username/repo
  ```

## Usage Notes

- All examples can be run from the root directory of the repository.
- Some examples require additional dependencies or API keys as noted above.
- Output files (like JSON maps) will be created in the current working directory.

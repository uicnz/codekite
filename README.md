# CodeKite Code Intelligence Toolkit

`codekite` is a modular, production-grade Python toolkit for codebase mapping, symbol extraction, code search, and building LLM-powered developer tools, agents, and workflows.

Use `codekite` to build things like code reviewers, code generators, even IDEs, all enriched with the right code context.

## Quick Installation

### Install from PyPI

```sh
# Installation (includes all features)
pip install codekite # not implemented yet
```

### Install from Source

```sh
git clone https://github.com/shaneholloman/codekite.git
cd codekite
uv sync
uv pip install -e .
```

## Basic Usage

```python
from codekite import Repository

# Load a local repository
repo = Repository("/path/to/your/local/codebase")

# Load a remote public GitHub repo
# repo = Repository("https://github.com/owner/repo")

# Explore the repo
print(repo.get_file_tree())
# Output: [{"path": "src/main.py", "is_dir": False, ...}, ...]

print(repo.extract_symbols('src/main.py'))
# Output: [{"name": "main", "type": "function", "file": "src/main.py", ...}, ...]
```

## Key Features & Capabilities

`codekite` helps your apps and agents deeply understand and interact with codebases, providing the core components to build your own AI-powered developer tools. Here are just a few of the things you can do:

- **Explore Code Structure:**

  - Get a bird's-eye view with `repo.get_file_tree()` to list all files and directories.
  - Dive into specifics with `repo.extract_symbols()` to identify all functions, classes, and other code constructs, either across the entire repository or within a single file.

- **Pinpoint Information:**

  - Perform precise textual or regular expression searches across your codebase using `repo.search_text()`.
  - Track down every definition and reference of a specific symbol (like a function or class) with `repo.find_symbol_usages()`.

- **Prepare Code for LLMs & Analysis:**

  - Break down large files into manageable pieces for LLM context windows using `repo.chunk_file_by_lines()` or `repo.chunk_file_by_symbols()`.
  - Instantly grab the full definition of a function or class just by knowing a line number within it using `repo.extract_context_around_line()`.

- **Generate Code Summaries (Alpha):**

  - Leverage LLMs to create natural language summaries for files, functions, or classes using the `Summarizer` (e.g., `summarizer.summarize_file()`, `summarizer.summarize_function()`).
  - Build a searchable semantic index of these AI-generated docstrings with `DocstringIndexer` and query it with `SummarySearcher` to find code based on intent and meaning.

- **And much more...** `codekite` also offers capabilities for semantic search on raw code, building custom context for LLMs, and more.

## License

MIT License

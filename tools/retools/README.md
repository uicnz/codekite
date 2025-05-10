# Warpflow Refactoring Tools

> [!IMPORTANT]
> REFACTOR THESE TOOLS TO BE MORE GENERIC

This directory contains Python tools for refactoring the codebase from "Langflow" to "Warpflow". These tools replace the original shell scripts and provide enhanced functionality with rich output formatting.

## Tools Overview

### Core Namespace Refactoring Tools

- **find_names.py** - Identifies files and directories containing "langflow" in their names
- **find_content.py** - Searches for "langflow" occurrences in file contents
- **replace_content.py** - Replaces "langflow" with "warpflow" in file contents
- **rename_files.py** - Renames files and directories from "langflow" to "warpflow"

### Organization Name Refactoring Tools

- **find_org_references.py** - Searches for all occurrences of "langflow-ai" organization name
- **replace_org_references.py** - Replaces "langflow-ai" with "shaneholloman" across the codebase

## Usage

All tools should be run using the project's `uv` environment:

```sh
# Organization Name Refactoring (MUST BE DONE FIRST)
uv run tools/find_org_references.py     # Find all "langflow-ai" organization references
uv run tools/replace_org_references.py  # Replace "langflow-ai" with "shaneholloman"

# Core Namespace Refactoring
uv run tools/find_names.py        # Find files/directories with "langflow" in their names
uv run tools/find_content.py      # Find occurrences of "langflow" in file contents
uv run tools/replace_content.py   # Replace "langflow" with "warpflow" in file contents
uv run tools/rename_files.py      # Rename files/directories containing "langflow"
```

## Features

- **Case Preservation**: Each case variant is handled correctly (langflow → warpflow, Langflow → Warpflow, LANGFLOW → WARPFLOW)
- **Dry-Run Mode**: Preview changes before applying them
- **Git-Based Workflow**: Designed to work with Git branches and commits instead of creating backup files
- **Rich Output**: Detailed tables and tree views of changes
- **Safety Features**: Tools directory is excluded from processing to avoid self-modification
- **Error Handling**: Specific handling for file system errors

## Recommended Workflow

### Important: Organization References Must Be Handled First

1. **Organization Name Changes**: First identify and replace organization references

    ```sh
    # Find all organization references
    uv run tools/find_org_references.py

    # Replace organization references (after forking/migrating repositories)
    uv run tools/replace_org_references.py
    ```

2. **Namespace Analysis**: Analyze the scope of namespace changes

    ```sh
    uv run tools/find_names.py
    uv run tools/find_content.py
    ```

3. **Namespace Content Replacement**: Replace namespace in file contents

    ```sh
    uv run tools/replace_content.py
    ```

4. **File/Directory Renaming**: Rename files and directories

    ```sh
    uv run tools/rename_files.py
    ```

5. **Verification**: After refactoring, run tests to verify everything works

### Why Organization References Must Be Changed First

If namespace changes (langflow → warpflow) were done before organization references (langflow-ai → shaneholloman), it would create hybrid references like "github.com/langflow-ai/warpflow" that would be missed in subsequent searches and lead to broken references.

## Implementation Details

- The refactoring tools exclude the `tools` directory itself to prevent self-modification
- Each tool creates detailed, color-coded output for easy analysis
- The `replace_content.py` and `rename_files.py` tools operate in a two-phase approach:
    1. First analyze changes without applying them
    2. Present a confirmation prompt before applying changes
- Use Git commits between refactoring phases to track changes instead of creating backup files

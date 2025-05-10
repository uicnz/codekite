# Warpflow Refactoring Tools

> [!NOTE]
> This projects needs to be made more generic.

This directory contains Python tools for refactoring the codebase from "OldNameSpace" to "NewNameSpace". These tools replace the original shell scripts and provide enhanced functionality with rich output formatting.

## Tools Overview

### Core Namespace Refactoring Tools

- **find_names.py** - Identifies files and directories containing "old-term" in their names
- **find_content.py** - Searches for "old-term" occurrences in file contents
- **replace_content.py** - Replaces "old-term" with "new-term" in file contents
- **rename_files.py** - Renames files and directories from "old-term" to "new-term"

### Organization Name Refactoring Tools

- **find_org_references.py** - Searches for all occurrences of "old-term" organization name
- **replace_org_references.py** - Replaces "old-term" with "new-term" across the codebase

## Usage

All tools should be run using the project's `uv` environment:

```sh
# Organization Name Refactoring (MUST BE DONE FIRST)
uv run tools/find_org_references.py     # Find all "old-term" organization references
uv run tools/replace_org_references.py  # Replace "old-term" with "new-term" organization references

# Core Namespace Refactoring
uv run tools/find_names.py        # Find files/directories with "old-term" in their names
uv run tools/find_content.py      # Find occurrences of "old-term" in file contents
uv run tools/replace_content.py   # Replace "old-term" with "new-term" in file contents
uv run tools/rename_files.py      # Rename files/directories containing "old-term"
```

## Features

- **Case Preservation**: Each case variant is handled correctly (old-term → new-term, OldTerm → NewTerm, OLD_TERM → NEW_TERM)
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

If namespace changes (oldnamespace → newnamespace) were done before organization references (old-term → new-term), it would create hybrid references like "github.com/old-term/new-term" that would be missed in subsequent searches and lead to broken references.

## Implementation Details

- The refactoring tools exclude the `tools` directory itself to prevent self-modification
- Each tool creates detailed, color-coded output for easy analysis
- The `replace_content.py` and `rename_files.py` tools operate in a two-phase approach:
    1. First analyze changes without applying them
    2. Present a confirmation prompt before applying changes
- Use Git commits between refactoring phases to track changes instead of creating backup files

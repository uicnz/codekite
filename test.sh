#!/bin/bash
# test.sh: Run all tests in the correct environment
set -e

# Set Python path to the local src directory
export PYTHONPATH=src
export KIT_TREE_SITTER_LIB="build/my-languages.so"

# Run tests with uv if available, else fallback to python
if command -v uv &> /dev/null; then
  uv run pytest -v tests
else
  python -m pytest -v tests
fi

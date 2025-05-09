#!/bin/bash
# Run mypy type checks for all source and test code
export PYTHONPATH=src
mypy src/codekite
mypy tests
mypy examples
mypy scripts

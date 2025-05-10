#!/usr/bin/env python
"""
Example showing how to use CodeKite's MCP server to analyze a repository.

This example demonstrates how to:
1. Connect to the CodeKite MCP server
2. Open a repository
3. Search for code
4. Build context for an LLM
5. Access repository structure and summary information

Usage:
  # Start the MCP server in one terminal:
  $ codekite mcp-serve

  # Run this example in another terminal:
  $ python examples/example_mcp_integration.py
"""

import asyncio
import json
from pathlib import Path
from fastmcp import Client

# Define our async main function
async def main():
    print("[INFO] Connecting to CodeKite MCP server...")

    # Connect to the running MCP server
    # By default, we connect to the stdio transport
    # client = Client("stdio://localhost")

    # For the HTTP transport, use:
    client = Client("http://localhost:8000/mcp")

    # For the SSE transport, use:
    # client = Client("http://localhost:8000")

    # Open the current repository (or any other local or remote repository)
    current_dir = str(Path.cwd())
    print(f"[INFO] Opening repository at {current_dir}...")

    result = await client.tools.open_repository(
        path_or_url=current_dir
    )
    repo_id = result["id"]
    print(f"[PASS] Repository opened with ID: {repo_id}")

    # Search for code in the repository
    print("[INFO] Searching for async functions...")
    search_results = await client.tools.search_code(
        repo_id=repo_id,
        query="async def",
        file_pattern="*.py"
    )

    print(f"[PASS] Found {len(search_results)} async functions:")
    for i, result in enumerate(search_results[:5]):  # Show first 5 results
        print(f"  {i+1}. {result['file']}:{result['line_number']}: {result['line'].strip()}")

    if len(search_results) > 5:
        print(f"  ... and {len(search_results) - 5} more")

    # Build context for an LLM
    print("[INFO] Building context for LLM...")
    context_result = await client.tools.build_context(
        repo_id=repo_id,
        query="How does repository structure work?",
        max_tokens=1000
    )

    # Print the first few lines of the context
    context_lines = context_result["context"].split("\n")
    print(f"[PASS] Built context ({len(context_lines)} lines):")
    for line in context_lines[:5]:  # First 5 lines
        print(f"  {line}")
    print("  ...")

    # Access repository structure
    print("[INFO] Fetching repository structure...")
    structure = await client.resources.read("repository://" + repo_id + "/structure")

    # Print high-level structure info
    file_count = len([f for f in structure["files"] if f.get("type") == "file"])
    dir_count = len([d for d in structure["files"] if d.get("type") == "directory"])
    print(f"[PASS] Repository structure: {file_count} files, {dir_count} directories")

    # Access repository summary
    print("[INFO] Fetching repository summary...")
    summary = await client.resources.read("repository://" + repo_id + "/summary")

    # Print the summary
    print("[PASS] Repository summary:")
    print(f"  Path: {summary['path']}")
    print(f"  File count: {summary['file_count']}")
    print(f"  Last updated: {summary['last_updated']}")
    print(f"  Languages: {json.dumps(summary['language_stats'], indent=2)}")

    # Get docstrings
    print("[INFO] Fetching repository docstrings...")
    docstrings = await client.resources.read("repository://" + repo_id + "/docstrings")

    print(f"[PASS] Found {len(docstrings)} docstrings")

    print("[INFO] Done!")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())

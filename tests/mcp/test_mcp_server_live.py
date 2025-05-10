#!/usr/bin/env python
"""
Test for connecting to a live CodeKite MCP server.

This test assumes an MCP server is already running on port 8001.
It connects to the server and tests all core functionality:
- Repository opening
- Code searching
- Structure retrieval
- Summary information

Usage:
  $ python test_mcp_server_live.py
"""

import asyncio
import json
import sys
from pathlib import Path
from fastmcp import Client

def print_content(content, max_entries=None):
    """Print content returned from MCP server.

    Args:
        content: Content returned from the MCP server
        max_entries: Maximum number of entries to display
    """
    if not content:
        print("  No content returned")
        return

    try:
        if isinstance(content, list):
            for i, item in enumerate(content):
                if max_entries and i >= max_entries:
                    print(f"  ... and {len(content) - max_entries} more items")
                    break

                if hasattr(item, "text"):
                    # Try to prettify JSON
                    try:
                        data = json.loads(item.text)
                        print(f"  {json.dumps(data, indent=2)[:500]}...")
                    except (json.JSONDecodeError, ValueError):
                        print(f"  {item.text[:500]}...")
                else:
                    print(f"  {str(item)[:500]}...")
        else:
            print(f"  {str(content)[:500]}...")
    except Exception as e:
        print(f"  Error displaying content: {e}")

async def main():
    # Connect to the running server
    async with Client("http://localhost:8001/mcp") as client:
        # Check server availability
        if not await client.ping():
            print("[FAIL] Server not responding")
            return 1

        # List tools and resources
        tools = await client.list_tools()
        required_tool = "codekite_open_repository"
        if not any(t.name == required_tool for t in tools):
            print(f"[FAIL] Required tool '{required_tool}' not found")
            return 1

        # Test 1: Open repository
        try:
            result = await client.call_tool(required_tool, {"path_or_url": str(Path.cwd())})
            repo_id = _extract_repo_id(result)
            if not repo_id:
                print("[FAIL] Could not get repository ID")
                return 1

            # Test 2: Search code
            search_results = await client.call_tool("codekite_search_code",
                                  {"repo_id": repo_id, "query": "def", "file_pattern": "*.py"})
            print("[PASS] Code search completed:")
            print_content(search_results, max_entries=3)

            # Test 3: Get repository structure
            structure = await client.read_resource(f"codekite://repository/{repo_id}/structure")
            print("[PASS] Structure retrieved:")
            print_content(structure, max_entries=5)

            # Test 4: Get repository summary
            summary = await client.read_resource(f"codekite://repository/{repo_id}/summary")
            print("[PASS] Summary retrieved:")
            print_content(summary)

            print("\n[PASS] All tests passed!")
            return 0
        except Exception as e:
            print(f"[FAIL] Test failed: {e}")
            return 1

def _extract_repo_id(result):
    """Extract repository ID from result."""
    if not (isinstance(result, list) and len(result) > 0):
        return None
    content = result[0]
    if not hasattr(content, "text"):
        return None
    try:
        return json.loads(content.text).get("id")
    except (json.JSONDecodeError, AttributeError):
        return None

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

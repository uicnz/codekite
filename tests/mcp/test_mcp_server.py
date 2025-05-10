#!/usr/bin/env python
"""
Test for CodeKite MCP server designed for automated testing.

This test is designed for running against the CodeKite MCP server in CI/CD environments.
The current implementation connects to an already running server on port 8000,
but contains the framework for self-contained server startup/shutdown that
could be re-enabled for true CI/CD testing.

The test covers:
- Repository opening
- Code searching
- Structure retrieval
- Summary information

Usage:
  $ python test_mcp_server.py
"""

import asyncio
import json
import subprocess
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

# Define server check methods
async def _ping_check(client):
    """Check server availability using ping."""
    return await client.ping()

async def _tools_check(client):
    """Check server availability by listing tools."""
    tools = await client.list_tools()
    return len(tools) > 0

async def _resources_check(client):
    """Check server availability by listing resources."""
    resources = await client.list_resources()
    return True

async def wait_for_server(url, max_attempts=25, delay=2.0):
    """Wait for the server to become available."""
    print(f"[INFO] Waiting for server at {url} to become available...")

    # Try different methods to check if server is up
    server_methods = [
        _ping_check,      # Method 1: Simple ping
        _tools_check,     # Method 2: List tools (sometimes works when ping doesn't)
        _resources_check  # Method 3: List resources (another alternative check)
    ]

    for attempt in range(max_attempts):
        # Try different methods in sequence
        for method_num, check_method in enumerate(server_methods):
            try:
                async with Client(url) as client:
                    if await check_method(client):
                        print(f"[PASS] Server is running and responding (method {method_num+1})")
                        return True
            except Exception as e:
                error_msg = str(e)
                if len(error_msg) > 100:
                    error_msg = error_msg[:100] + "..."

                if attempt % 5 == 0:  # Only show errors every 5 attempts to reduce noise
                    print(f"[WAIT] Method {method_num+1} failed (attempt {attempt+1}/{max_attempts}): {error_msg}")

        # If we get here, all methods failed
        print(f"[WAIT] Server not ready, waiting (attempt {attempt+1}/{max_attempts})...")
        await asyncio.sleep(delay)

    print("[FAIL] Server failed to start or respond after multiple attempts")
    return False

async def run_tests():
    """Run tests against the MCP server."""
    # Test with Streamable HTTP transport
    async with Client("http://localhost:8002/mcp") as client:
        # Check server availability
        if not await client.ping():
            print("[FAIL] Server not responding")
            return False

        # List tools and resources
        tools = await client.list_tools()
        required_tool = "codekite_open_repository"
        if not any(t.name == required_tool for t in tools):
            print(f"[FAIL] Required tool '{required_tool}' not found")
            return False

        # Test 1: Open repository
        try:
            result = await client.call_tool(required_tool, {"path_or_url": str(Path.cwd())})
            repo_id = _extract_repo_id(result)
            if not repo_id:
                print("[FAIL] Could not get repository ID")
                return False

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
            return True
        except Exception as e:
            print(f"[FAIL] Test failed: {e}")
            return False

async def main():
    """Run main test."""
    # Skip the server startup and run tests directly against port 8000
    # This simplifies the test while we debug connection issues
    print("[INFO] Running tests against already running server on port 8000")

    # Run the tests
    try:
        # Use port 8000 where a server is already running
        async with Client("http://localhost:8000/mcp") as client:
            # Check server availability
            if not await client.ping():
                print("[FAIL] Server not responding")
                return 1

            print("[PASS] Connected to server successfully")

            # List tools and resources
            tools = await client.list_tools()
            required_tool = "codekite_open_repository"
            if not any(t.name == required_tool for t in tools):
                print(f"[FAIL] Required tool '{required_tool}' not found")
                return 1

            print("[PASS] Required tools found")

            # Test 1: Open repository
            try:
                result = await client.call_tool(required_tool, {"path_or_url": str(Path.cwd())})
                repo_id = _extract_repo_id(result)
                if not repo_id:
                    print("[FAIL] Could not get repository ID")
                    return 1

                print(f"[PASS] Repository opened with ID: {repo_id}")

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
    except Exception as e:
        print(f"[FAIL] Client connection error: {e}")
        return 1

    return 0

    # Note: This test is temporarily simplified to use an existing server instead
    # of starting its own. For CI/CD, we would need to reimplement the server
    # startup and monitoring logic.

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

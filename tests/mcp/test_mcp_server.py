#!/usr/bin/env python
"""
Test script for the CodeKite MCP server.

This script starts an MCP server in a subprocess and tests basic functionality
using a client to ensure everything works correctly.

Usage:
  $ python test_mcp_server.py
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from fastmcp import Client

async def wait_for_server(url, max_attempts=10, delay=0.5):
    """Wait for the server to become available."""
    for attempt in range(max_attempts):
        try:
            client = Client(url)
            # Just try to connect
            await client.resources.list_names()
            print("[PASS] Server is running and responding")
            return True
        except Exception:
            print(f"[WAIT] Waiting for server (attempt {attempt+1}/{max_attempts})...")
            await asyncio.sleep(delay)

    print("[FAIL] Server failed to start or respond")
    return False

async def run_tests():
    """Run tests against the MCP server."""
    # Test with Streamable HTTP transport
    client = Client("http://localhost:8000/mcp")

    # Test 1: Open a repository
    try:
        result = await client.tools.open_repository(
            path_or_url=str(Path.cwd())
        )
        repo_id = result.get("id")
        if repo_id:
            print(f"[PASS] Test 1: Successfully opened repository with ID: {repo_id}")
        else:
            print("[FAIL] Test 1: Failed to get repository ID")
            return False
    except Exception as e:
        print(f"[FAIL] Test 1: Failed to open repository: {e}")
        return False

    # Test 2: Search for code
    try:
        results = await client.tools.search_code(
            repo_id=repo_id,
            query="def",
            file_pattern="*.py"
        )
        if isinstance(results, list):
            print(f"[PASS] Test 2: Search returned {len(results)} results")
        else:
            print(f"[FAIL] Test 2: Search returned unexpected type: {type(results)}")
            return False
    except Exception as e:
        print(f"[FAIL] Test 2: Failed to search code: {e}")
        return False

    # Test 3: Access repository structure
    try:
        structure = await client.resources.read(f"repository://{repo_id}/structure")
        if isinstance(structure, dict) and "files" in structure:
            print("[PASS] Test 3: Successfully retrieved repository structure")
        else:
            print(f"[FAIL] Test 3: Unexpected structure response: {structure}")
            return False
    except Exception as e:
        print(f"[FAIL] Test 3: Failed to get repository structure: {e}")
        return False

    # Test 4: Access repository summary
    try:
        summary = await client.resources.read(f"repository://{repo_id}/summary")
        if isinstance(summary, dict) and "language_stats" in summary:
            print("[PASS] Test 4: Successfully retrieved repository summary")
        else:
            print(f"[FAIL] Test 4: Unexpected summary response: {summary}")
            return False
    except Exception as e:
        print(f"[FAIL] Test 4: Failed to get repository summary: {e}")
        return False

    print("[PASS] All tests passed!")
    return True

async def main():
    # Start the MCP server in a subprocess
    server_cmd = [sys.executable, "-m", "codekite", "mcp-serve", "--transport", "streamable-http", "--port", "8000"]
    print(f"[INFO] Starting MCP server with command: {' '.join(server_cmd)}")

    server_process = subprocess.Popen(
        server_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for the server to start
    server_ready = await wait_for_server("http://localhost:8000/mcp")
    if not server_ready:
        server_process.kill()
        print("[FAIL] Server failed to start, exiting")
        return 1

    # Run the tests
    try:
        success = await run_tests()
    finally:
        # Clean up the server process
        print("[INFO] Terminating server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

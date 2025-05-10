#!/usr/bin/env python
"""
Test script for the standalone CodeKite MCP server.

This script tests the already-running MCP server for basic functionality.

Usage:
  # First start the server in another terminal:
  # $ python standalone_mcp_server.py

  # Then run this test script:
  # $ python test_standalone_mcp.py
"""

import asyncio
import sys
import json
from pathlib import Path
from fastmcp import Client

async def run_tests():
    """Run tests against the MCP server."""
    print("[INFO] Connecting to standalone MCP server...")

    # Create the client and use it in a context manager
    client = Client("http://localhost:8000/mcp")

    async with client:
        # Verify connection
        print("[INFO] Connected to the server, listing available tools...")
        tools = await client.list_tools()
        print(f"[INFO] Found {len(tools)} available tools")

        # List tool names for debugging
        for tool in tools:
            print(f"  - {tool.name}")

        # Test 1: Open a repository
        try:
            print("[INFO] Opening repository...")
            result = await client.call_tool("open_repository", {
                "path_or_url": str(Path.cwd())
            })
            print(f"[DEBUG] Open repository result type: {type(result)}")
            print(f"[DEBUG] Open repository result: {result}")

            # Handle the TextContent result format
            if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                # Extract the JSON text from the TextContent object
                json_text = result[0].text
                # Parse the JSON text
                data = json.loads(json_text)
                if "id" in data:
                    repo_id = data["id"]
                    print(f"[PASS] Test 1: Successfully opened repository with ID: {repo_id}")
                else:
                    print(f"[FAIL] Test 1: Missing 'id' in response: {data}")
                    return False
            else:
                print(f"[FAIL] Test 1: Unexpected result format: {result}")
                return False
        except Exception as e:
            print(f"[FAIL] Test 1: Failed to open repository: {e}")
            return False

        # Test 2: Search for code
        try:
            print("[INFO] Searching for code...")
            result = await client.call_tool("search_code", {
                "repo_id": repo_id,
                "query": "def",
                "file_pattern": "*.py"
            })
            print(f"[DEBUG] Search result type: {type(result)}")

            # Handle the TextContent result format
            if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                # Extract the JSON text from the TextContent object
                json_text = result[0].text
                # Parse the JSON text
                results = json.loads(json_text)
                if isinstance(results, list):
                    print(f"[PASS] Test 2: Search returned {len(results)} results")
                else:
                    print(f"[FAIL] Test 2: Search result is not a list: {results}")
                    return False
            else:
                print(f"[FAIL] Test 2: Unexpected result format: {result}")
                return False
        except Exception as e:
            print(f"[FAIL] Test 2: Failed to search code: {e}")
            return False

        # Test 3: Access repository structure
        try:
            print("[INFO] Getting repository structure...")
            resource_result = await client.read_resource(f"repository://{repo_id}/structure")
            print(f"[DEBUG] Structure result type: {type(resource_result)}")

            # Handle resource result
            if hasattr(resource_result, 'content') and hasattr(resource_result.content, 'text'):
                json_text = resource_result.content.text
                structure = json.loads(json_text)
                if isinstance(structure, dict) and "files" in structure:
                    print("[PASS] Test 3: Successfully retrieved repository structure")
                else:
                    print(f"[FAIL] Test 3: Unexpected structure: {structure}")
                    return False
            else:
                print(f"[FAIL] Test 3: Unexpected structure response format: {resource_result}")
                return False
        except Exception as e:
            print(f"[FAIL] Test 3: Failed to get repository structure: {e}")
            return False

        # Test 4: Access repository summary
        try:
            print("[INFO] Getting repository summary...")
            resource_result = await client.read_resource(f"repository://{repo_id}/summary")
            print(f"[DEBUG] Summary result type: {type(resource_result)}")

            # Handle resource result
            if hasattr(resource_result, 'content') and hasattr(resource_result.content, 'text'):
                json_text = resource_result.content.text
                summary = json.loads(json_text)
                if isinstance(summary, dict) and "language_stats" in summary:
                    print("[PASS] Test 4: Successfully retrieved repository summary")
                else:
                    print(f"[FAIL] Test 4: Unexpected summary: {summary}")
                    return False
            else:
                print(f"[FAIL] Test 4: Unexpected summary response format: {resource_result}")
                return False
        except Exception as e:
            print(f"[FAIL] Test 4: Failed to get repository summary: {e}")
            return False

        print("[PASS] All tests passed!")
        return True

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)

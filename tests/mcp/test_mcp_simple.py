#!/usr/bin/env python
"""
Simplified MCP server test script.

This script tests the already-running MCP server with minimal output.
"""

import asyncio
import sys
import json
from pathlib import Path
from fastmcp import Client

async def run_tests():
    """Run tests against the MCP server with minimal output."""
    print("[INFO] Testing MCP server connection...")

    # Create the client and use it in a context manager
    client = Client("http://localhost:8000/mcp")

    async with client:
        # Verify connection and tools
        tools = await client.list_tools()
        if len(tools) < 2:
            print(f"[FAIL] Not enough tools available: found {len(tools)}")
            return False

        # Test 1: Open a repository
        try:
            result = await client.call_tool("open_repository", {
                "path_or_url": str(Path.cwd())
            })

            # Parse the result
            if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                data = json.loads(result[0].text)
                if "id" in data:
                    repo_id = data["id"]
                    print(f"[PASS] Repository opened with ID: {repo_id}")
                else:
                    print("[FAIL] Missing 'id' in repository response")
                    return False
            else:
                print("[FAIL] Unexpected repository response format")
                return False
        except Exception as e:
            print(f"[FAIL] Repository open error: {str(e)[:100]}")
            return False

        # Test 2: Search for code
        try:
            result = await client.call_tool("search_code", {
                "repo_id": repo_id,
                "query": "def",
                "file_pattern": "*.py"
            })

            # Parse the result
            if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                results = json.loads(result[0].text)
                if isinstance(results, list):
                    print(f"[PASS] Code search returned {len(results)} results")
                else:
                    print("[FAIL] Code search result is not a list")
                    return False
            else:
                print("[FAIL] Unexpected code search response format")
                return False
        except Exception as e:
            print(f"[FAIL] Code search error: {str(e)[:100]}")
            return False

        # Test 3: Access repository structure
        try:
            print("[INFO] Getting repository structure...")
            resource_uri = f"repository://{repo_id}/structure"
            resource_result = await client.read_resource(resource_uri)

            # Debug info
            print(f"[DEBUG] Structure result type: {type(resource_result)}")

            # Inspect list content if it's a list
            if isinstance(resource_result, list):
                print(f"[DEBUG] Structure list length: {len(resource_result)}")
                if len(resource_result) > 0:
                    print(f"[DEBUG] First item type: {type(resource_result[0])}")
                    print(f"[DEBUG] First item attributes: {dir(resource_result[0])}")

                    # If the first item has a text attribute, try to parse it
                    if hasattr(resource_result[0], 'text'):
                        print(f"[DEBUG] First item text sample: {resource_result[0].text[:100]}...")
                        try:
                            structure = json.loads(resource_result[0].text)
                            if isinstance(structure, dict) and "files" in structure:
                                print("[PASS] Repository structure retrieved successfully (list[0].text)")
                                # Continue with test 4
                                pass_test3 = True
                            else:
                                print("[FAIL] Invalid repository structure format in list[0].text")
                                pass_test3 = False
                        except Exception as e:
                            print(f"[FAIL] Error parsing structure data from list[0].text: {str(e)[:100]}")
                            pass_test3 = False
                    else:
                        print("[FAIL] List item does not have text attribute")
                        pass_test3 = False
                else:
                    print("[FAIL] Empty list returned for structure")
                    pass_test3 = False
            else:
                print("[FAIL] Unexpected structure response type")
                pass_test3 = False

            if not pass_test3:
                return False
        except Exception as e:
            print(f"[FAIL] Structure retrieval error: {str(e)[:100]}")
            return False

        # Test 4: Access repository summary
        try:
            print("[INFO] Getting repository summary...")
            resource_uri = f"repository://{repo_id}/summary"
            resource_result = await client.read_resource(resource_uri)

            # Debug info
            print(f"[DEBUG] Summary result type: {type(resource_result)}")

            # Inspect list content if it's a list
            if isinstance(resource_result, list):
                print(f"[DEBUG] Summary list length: {len(resource_result)}")
                if len(resource_result) > 0:
                    print(f"[DEBUG] First item type: {type(resource_result[0])}")

                    # If the first item has a text attribute, try to parse it
                    if hasattr(resource_result[0], 'text'):
                        print(f"[DEBUG] First item text sample: {resource_result[0].text[:100]}...")
                        try:
                            summary = json.loads(resource_result[0].text)
                            if isinstance(summary, dict) and "language_stats" in summary:
                                print("[PASS] Repository summary retrieved successfully (list[0].text)")
                                # All tests passed
                                pass_test4 = True
                            else:
                                print("[FAIL] Invalid repository summary format in list[0].text")
                                pass_test4 = False
                        except Exception as e:
                            print(f"[FAIL] Error parsing summary data from list[0].text: {str(e)[:100]}")
                            pass_test4 = False
                    else:
                        print("[FAIL] List item does not have text attribute")
                        pass_test4 = False
                else:
                    print("[FAIL] Empty list returned for summary")
                    pass_test4 = False
            else:
                print("[FAIL] Unexpected summary response type")
                pass_test4 = False

            if not pass_test4:
                return False
        except Exception as e:
            print(f"[FAIL] Summary retrieval error: {str(e)[:100]}")
            return False

        print("[PASS] All MCP tests passed!")
        return True

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)

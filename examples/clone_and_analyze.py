#!/usr/bin/env python
"""
Repository cloner and analyzer using CodeKite MCP.

This script clones the repository first, then uses the MCP client to analyze it locally.
"""

import asyncio
import json
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from fastmcp import Client

async def clone_and_analyze_repository(repo_url):
    """Clone and analyze a repository using CodeKite MCP tools."""
    print(f"[INFO] Analyzing repository: {repo_url}")

    # Create a temporary directory for cloning
    temp_dir = tempfile.mkdtemp()
    try:
        # Clone the repository
        print(f"[INFO] Cloning repository to {temp_dir}...")
        clone_result = subprocess.run(
            ["git", "clone", "--depth=1", repo_url, temp_dir],
            check=True,
            capture_output=True,
            text=True
        )
        print("[PASS] Repository cloned successfully")

        # Count files
        file_count = sum(1 for _ in Path(temp_dir).glob("**/*") if _.is_file() and not _.name.startswith('.'))
        print(f"[INFO] Found {file_count} files in repository")

        # Connect to the MCP server
        client = Client("http://localhost:8000/mcp")

        async with client:
            # Step 1: Open the repository (use local path)
            try:
                result = await client.call_tool("codekite_open_repository", {
                    "path_or_url": temp_dir
                })

                if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                    data = json.loads(result[0].text)
                    if "id" in data:
                        repo_id = data["id"]
                        print(f"[INFO] Repository opened with ID: {repo_id}")
                    else:
                        print("[ERROR] Missing 'id' in repository response")
                        return
                else:
                    print("[ERROR] Unexpected repository response format")
                    return
            except Exception as e:
                print(f"[ERROR] Repository open error: {str(e)[:100]}")
                return

            # Step 2: Get repository summary
            try:
                print("[INFO] Getting repository summary...")
                resource_uri = f"codekite://repository/{repo_id}/summary"
                summary_result = await client.read_resource(resource_uri)

                if isinstance(summary_result, list) and len(summary_result) > 0 and hasattr(summary_result[0], 'text'):
                    summary = json.loads(summary_result[0].text)
                    print("\n=== REPOSITORY SUMMARY ===")
                    print(f"Repository path: {summary.get('path', 'N/A')}")
                    print(f"File count: {summary.get('file_count', 0)}")

                    # Language statistics
                    if 'language_stats' in summary:
                        print("\nLanguage distribution:")
                        for lang, count in summary['language_stats'].items():
                            print(f"  {lang}: {count} files")

                    print(f"Last updated: {summary.get('last_updated', 'N/A')}")
                    print("===========================\n")
                else:
                    print("[ERROR] Failed to get repository summary")
            except Exception as e:
                print(f"[ERROR] Summary retrieval error: {str(e)[:100]}")

            # Step 3: Get repository structure
            try:
                print("[INFO] Getting repository structure...")
                resource_uri = f"codekite://repository/{repo_id}/structure"
                structure_result = await client.read_resource(resource_uri)

                if isinstance(structure_result, list) and len(structure_result) > 0 and hasattr(structure_result[0], 'text'):
                    structure = json.loads(structure_result[0].text)
                    print("\n=== REPOSITORY STRUCTURE ===")
                    if 'files' in structure:
                        # Create directory tree
                        dirs = [item for item in structure['files'] if item.get('type') == 'directory']
                        dirs.sort(key=lambda x: x.get('path', ''))
                        files = [item for item in structure['files'] if item.get('type') == 'file']
                        files.sort(key=lambda x: x.get('path', ''))

                        print("\nDirectories:")
                        for d in dirs[:20]:  # Limit to top 20 directories
                            print(f"  /{d.get('path', '')}")

                        if len(dirs) > 20:
                            print(f"  ... and {len(dirs) - 20} more directories")

                        print("\nKey files:")
                        key_files = [f for f in files if f.get('name', '').lower() in
                                     ('readme.md', 'setup.py', 'pyproject.toml', 'package.json',
                                      'main.py', 'index.js', 'app.py', 'app.js', 'requirements.txt')]
                        for f in key_files:
                            print(f"  /{f.get('path', '')}")

                        print(f"\nTotal directories: {len(dirs)}")
                        print(f"Total files: {len(files)}")
                    print("============================\n")
                else:
                    print("[ERROR] Failed to get repository structure")
            except Exception as e:
                print(f"[ERROR] Structure retrieval error: {str(e)[:100]}")

            # Step 4: Perform code search for key patterns
            try:
                print("[INFO] Performing code searches...")

                # Search for Python classes
                class_result = await client.call_tool("codekite_search_code", {
                    "repo_id": repo_id,
                    "query": "class\\s+\\w+",
                    "file_pattern": "*.py"
                })

                if isinstance(class_result, list) and len(class_result) > 0 and hasattr(class_result[0], 'text'):
                    classes = json.loads(class_result[0].text)
                    print(f"\nFound {len(classes)} Python classes")

                    if len(classes) > 0:
                        print("\nSample classes:")
                        for cls in classes[:5]:  # Show top 5 classes
                            print(f"  {cls.get('file', '')}, Line {cls.get('line_number', '')}: {cls.get('line', '').strip()}")

                # Search for Python functions
                function_result = await client.call_tool("codekite_search_code", {
                    "repo_id": repo_id,
                    "query": "def\\s+\\w+",
                    "file_pattern": "*.py"
                })

                if isinstance(function_result, list) and len(function_result) > 0 and hasattr(function_result[0], 'text'):
                    functions = json.loads(function_result[0].text)
                    print(f"\nFound {len(functions)} Python functions")

                    if len(functions) > 0:
                        print("\nSample functions:")
                        for func in functions[:5]:  # Show top 5 functions
                            print(f"  {func.get('file', '')}, Line {func.get('line_number', '')}: {func.get('line', '').strip()}")

                # Search for JavaScript/TypeScript functions
                js_function_result = await client.call_tool("codekite_search_code", {
                    "repo_id": repo_id,
                    "query": "function\\s+\\w+|\\w+\\s*=\\s*function|\\w+\\s*=>",
                    "file_pattern": "*.{js,ts,jsx,tsx}"
                })

                if isinstance(js_function_result, list) and len(js_function_result) > 0 and hasattr(js_function_result[0], 'text'):
                    js_functions = json.loads(js_function_result[0].text)
                    print(f"\nFound {len(js_functions)} JavaScript/TypeScript functions")

                    if len(js_functions) > 0:
                        print("\nSample JS/TS functions:")
                        for func in js_functions[:5]:  # Show top 5 functions
                            print(f"  {func.get('file', '')}, Line {func.get('line_number', '')}: {func.get('line', '').strip()}")
            except Exception as e:
                print(f"[ERROR] Code search error: {str(e)[:100]}")

            # Step 5: Generate context
            try:
                print("\n[INFO] Building comprehensive context...")

                context_result = await client.call_tool("codekite_build_context", {
                    "repo_id": repo_id,
                    "query": "main functionality",
                    "max_tokens": 8000
                })

                if isinstance(context_result, list) and len(context_result) > 0 and hasattr(context_result[0], 'text'):
                    context_data = json.loads(context_result[0].text)
                    if "context" in context_data:
                        context = context_data["context"]
                        print("\n=== REPOSITORY CONTEXT ===")
                        print(context[:1500] + "...\n[Context truncated]" if len(context) > 1500 else context)
                        print("===========================\n")
                else:
                    print("[ERROR] Failed to build context")
            except Exception as e:
                print(f"[ERROR] Context building error: {str(e)[:100]}")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Git clone failed: {e.stderr}")
    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
    finally:
        # Clean up the temporary directory
        print(f"[INFO] Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python clone_and_analyze.py <repository_url>")
        sys.exit(1)

    repo_url = sys.argv[1]
    asyncio.run(clone_and_analyze_repository(repo_url))

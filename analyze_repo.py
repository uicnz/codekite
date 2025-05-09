#!/usr/bin/env python
"""
Repository analyzer using CodeKit MCP.

This script uses the MCP client to analyze a GitHub repository.
"""

import asyncio
import json
import sys
import argparse
from fastmcp import Client

async def analyze_repository(repo_url, search_query=None, max_results=10):
    """Analyze a repository using CodeKit MCP tools."""
    print(f"[INFO] Analyzing repository: {repo_url}")
    client = Client("http://localhost:8000/mcp")

    async with client:
        # Step 1: Open the repository
        try:
            result = await client.call_tool("codekite_open_repository", {
                "path_or_url": repo_url
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

            # Search for classes
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

            # Search for functions
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
        except Exception as e:
            print(f"[ERROR] Code search error: {str(e)[:100]}")

        # Step 5: Perform custom search if specified
        if search_query:
            try:
                print(f"\n[INFO] Searching for: '{search_query}'...")

                search_result = await client.call_tool("codekite_search_code", {
                    "repo_id": repo_id,
                    "query": search_query,
                    "file_pattern": "*"
                })

                if isinstance(search_result, list) and len(search_result) > 0 and hasattr(search_result[0], 'text'):
                    results = json.loads(search_result[0].text)
                    print(f"\n=== SEARCH RESULTS FOR '{search_query}' ===")
                    print(f"Found {len(results)} matches")

                    if len(results) > 0:
                        print("\nTop matches:")
                        for i, result in enumerate(results[:max_results]):
                            print(f"\n{i+1}. {result.get('file', '')}, Line {result.get('line_number', '')}")
                            print(f"   {result.get('line', '').strip()}")
                    print("===========================\n")
                else:
                    print(f"[INFO] No results found for '{search_query}'")
            except Exception as e:
                print(f"[ERROR] Search error: {str(e)[:100]}")

        # Step 6: Generate context
        try:
            print("\n[INFO] Building comprehensive context...")

            context_result = await client.call_tool("codekite_build_context", {
                "repo_id": repo_id,
                "query": search_query or "main functionality",
                "max_tokens": 8000
            })

            if isinstance(context_result, list) and len(context_result) > 0 and hasattr(context_result[0], 'text'):
                context_data = json.loads(context_result[0].text)
                if "context" in context_data:
                    context = context_data["context"]
                    print(f"\n=== REPOSITORY CONTEXT FOR '{search_query or 'main functionality'}' ===")
                    print(context[:1000] + "...\n[Context truncated]" if len(context) > 1000 else context)
                    print("===========================\n")
            else:
                print("[ERROR] Failed to build context")
        except Exception as e:
            print(f"[ERROR] Context building error: {str(e)[:100]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a GitHub repository using CodeKit MCP")
    parser.add_argument("repository_url", help="URL of the repository to analyze")
    parser.add_argument("--search", help="Search query for specific functionality", default="main functionality")
    parser.add_argument("--max-results", type=int, help="Maximum number of search results to display", default=10)

    args = parser.parse_args()
    asyncio.run(analyze_repository(args.repository_url, args.search, args.max_results))

"""
Semantic Code Search using Kit

This script demonstrates Kit's semantic search capabilities for finding code
based on natural language queries or code snippets.
"""
from kit import Repository
import argparse
import json
import sys

def semantic_search(repo_path: str, query: str, limit: int = 10) -> list:
    """
    Perform semantic search on repository code.

    Args:
        repo_path: Path to the repository to search
        query: Natural language query or code snippet
        limit: Maximum number of results to return

    Returns:
        List of search results with file, relevance score, and code context
    """
    print(f"Initializing repository at {repo_path}...")
    repo = Repository(repo_path)

    print(f"Performing semantic search for: \"{query}\"")
    # Use the built-in semantic search capability of Kit
    try:
        # Try different parameter options (API might have changed)
        try:
            results = repo.search_semantic(query)
        except TypeError:
            try:
                # Try with different parameter name
                results = repo.search_semantic(query=query)
            except Exception:
                # Try with no parameters (just use default behavior)
                results = repo.search_semantic()

        # Limit results manually
        results = results[:limit]

        # Add additional context to results
        enhanced_results = []
        for result in results:
            file_path = result.get("file")

            # Get full context for search results
            if "symbol" in result:
                symbol_name = result["symbol"]
                symbol_info = repo.extract_symbols(file_path)
                symbol_details = next((s for s in symbol_info if s["name"] == symbol_name), None)
                if symbol_details:
                    result["code"] = symbol_details.get("code", "Code not available")
                    result["type"] = symbol_details.get("type", "Unknown")

            # If just a file result, get first few lines
            elif not result.get("code") and file_path:
                try:
                    content = repo.get_file_content(file_path)
                    result["code"] = "\n".join(content.split("\n")[:10]) + "\n..."
                except Exception:
                    result["code"] = "Unable to read file content"

            enhanced_results.append(result)

        return enhanced_results
    except Exception as e:
        print(f"Error during semantic search: {str(e)}")
        print("Falling back to keyword search...")

        # Use standard text search as fallback
        try:
            print(f"Performing keyword search for: \"{query}\"")
            text_results = repo.search_text(query)

            if text_results:
                enhanced_results = []
                for result in text_results[:limit]:
                    file_path = result.get("file")
                    context = []

                    if "context_before" in result:
                        context.extend(result["context_before"])

                    if "line" in result:
                        context.append(result["line"])

                    if "context_after" in result:
                        context.extend(result["context_after"])

                    result["code"] = "\n".join(context)
                    result["score"] = 0.5  # Arbitrary score for text match
                    enhanced_results.append(result)

                return enhanced_results
        except Exception as search_err:
            print(f"Text search also failed: {str(search_err)}")
            print("Falling back to simple file scan...")

        # Last resort - manual search
        results = []

        # Get all Python files
        for file in repo.get_file_tree():
            if file.get("is_dir", False) or not file["path"].endswith((".py", ".md")):
                continue

            file_path = file["path"]
            try:
                content = repo.get_file_content(file_path)

                # Skip files that are too large
                if len(content) > 100000:  # Skip files larger than ~100KB
                    continue

                # Check if query appears in content
                if query.lower() in content.lower():
                    # Find the relevant line with the query
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if query.lower() in line.lower():
                            context_start = max(0, i-2)
                            context_end = min(len(lines), i+3)
                            context_str = "\n".join(lines[context_start:context_end])
                            results.append({
                                "file": file_path,
                                "line_number": i+1,
                                "code": context_str,
                                "score": 0.5  # Arbitrary score for text match
                            })
                            break

                # Check symbols if it's a Python file
                if file_path.endswith(".py"):
                    try:
                        symbols = repo.extract_symbols(file_path)
                        for symbol in symbols:
                            if (query.lower() in symbol["name"].lower() or
                                (symbol.get("code") and query.lower() in symbol["code"].lower())):
                                results.append({
                                    "file": file_path,
                                    "symbol": symbol["name"],
                                    "type": symbol["type"],
                                    "code": symbol.get("code", "No code available"),
                                    "score": 0.7  # Slightly higher score for symbol match
                                })
                    except Exception:
                        pass  # Skip symbol extraction if it fails
            except Exception:
                pass  # Skip files that can't be read

        return results[:limit]

def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic code search using Kit.")
    parser.add_argument("--repo", required=True, help="Path to the code repository")
    parser.add_argument("--query", required=True, help="Search query (keyword or phrase)")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results")
    parser.add_argument("--output", help="Output file for results (JSON)")
    args = parser.parse_args()

    results = semantic_search(args.repo, args.query, args.limit)

    if not results:
        print("No matches found for your query.")
        sys.exit(0)

    print(f"\nFound {len(results)} results:")

    # Print results in a readable format
    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"File: {result.get('file', 'Unknown')}")
        if "symbol" in result:
            print(f"Symbol: {result['symbol']} ({result.get('type', 'unknown type')})")
        if "line_number" in result:
            print(f"Line: {result['line_number']}")
        elif "line" in result and isinstance(result["line"], int):
            print(f"Line: {result['line']}")
        if "score" in result:
            print(f"Relevance: {result['score']:.2f}")
        print("\nCode:")
        print("```")
        print(result.get("code", "No code available"))
        print("```")

    # Save to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults also saved to {args.output}")

if __name__ == "__main__":
    main()

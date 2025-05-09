"""
Semantic Code Search using Kit

This script demonstrates Kit's semantic search capabilities for finding code
based on natural language queries or code snippets.
"""
from kit import Repository
import argparse
import json
import os
import sys

def semantic_search(repo_path: str, query: str, limit: int = 10, embed_fn=None) -> list:
    """
    Perform semantic search on repository code.

    Args:
        repo_path: Path to the repository to search
        query: Natural language query or code snippet
        limit: Maximum number of results to return
        embed_fn: Optional embedding function for semantic search

    Returns:
        List of search results with file, relevance score, and code context
    """
    print(f"Initializing repository at {repo_path}...")
    repo = Repository(repo_path)

    # Get a list of source files to focus on
    file_tree = repo.get_file_tree()
    source_files = [f for f in file_tree if not f.get("is_dir", False) and
                   f["path"].endswith((".py", ".md", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".go", ".rs", ".sql"))]

    print(f"Found {len(source_files)} source files for analysis")
    print(f"Performing search for: \"{query}\"")
    # Define a file filter function to exclude certain files
    def should_include_file(file_path):
        # If path is None, can't check it
        if not file_path:
            return True

        # Skip directories we're definitely not interested in
        excluded_dirs = [".git/", ".github/", "__pycache__/", "node_modules/"]
        for excluded_dir in excluded_dirs:
            if excluded_dir in file_path:
                return False

        # Lower priority for repo_map.json but don't exclude entirely
        # (only exclude it if we find enough other results)
        return True

    # Use the built-in semantic search capability of Kit
    try:
        # Try different parameter options (API might have changed)
        try:
            if embed_fn:
                results = repo.search_semantic(query, embed_fn=embed_fn)
            else:
                results = repo.search_semantic(query)
        except TypeError:
            try:
                # Try with different parameter name
                if embed_fn:
                    results = repo.search_semantic(query=query, embed_fn=embed_fn)
                else:
                    results = repo.search_semantic(query=query)
            except Exception:
                # If everything else fails, use default behavior
                results = repo.search_semantic()

        # Limit results manually
        results = results[:limit]

        # Add additional context to results
        enhanced_results = []
        for result in results:
            file_path = result.get("file")

            # Skip excluded files
            if file_path and not should_include_file(file_path):
                continue

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

                    # Skip excluded files
                    if file_path and not should_include_file(file_path):
                        continue

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

        # Filter to only source code files
        for file in repo.get_file_tree():
            # Skip directories and non-source files
            if file.get("is_dir", False) or not file["path"].endswith((".py", ".md", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".go", ".rs", ".sql")):
                continue

            file_path = file["path"]

            # Skip excluded files
            if not should_include_file(file_path):
                continue
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

def format_output(title, content):
    """Helper function to format search output in a more readable way"""
    print(f"\n{'=' * 80}")
    print(f"=== {title} ===")
    print(f"{'=' * 80}")

    if isinstance(content, list):
        for i, item in enumerate(content[:5], 1):
            print(f"\n[Result {i}]")
            if isinstance(item, dict):
                for key, value in item.items():
                    if key == "code":
                        print(f"\n{key.capitalize()}:")
                        print("```")
                        print(value)
                        print("```")
                    else:
                        print(f"{key.capitalize()}: {value}")
            else:
                print(item)

        if len(content) > 5:
            print(f"\n... and {len(content) - 5} more results")
    else:
        print(content)

def setup_openai_embed_fn():
    """Try to set up an OpenAI embedding function if the API key is available"""
    try:
        import openai
        from openai import OpenAI

        # Check if API key is available in environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None

        # Create OpenAI client
        client = OpenAI()

        # Define embedding function
        def embed_fn(text):
            try:
                response = client.embeddings.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"Error generating embeddings: {e}")
                return None

        return embed_fn
    except ImportError:
        return None

def direct_repo_map_search(repo_path, search_term):
    """
    Directly search in repo_map.json as a fallback since we know it exists
    and contains code samples
    """
    try:
        repo_map_path = os.path.join(repo_path, "repo_map.json")
        if os.path.exists(repo_map_path):
            print(f"Searching directly in repo_map.json for '{search_term}'...")
            with open(repo_map_path, 'r') as f:
                content = f.read()

            if search_term.lower() in content.lower():
                print(f"Found match for '{search_term}' in repo_map.json!")

                # Find some context around the match
                lines = content.split('\n')
                results = []
                for i, line in enumerate(lines):
                    if search_term.lower() in line.lower():
                        # Get 5 lines of context (or fewer if we hit the boundaries)
                        context_start = max(0, i-2)
                        context_end = min(len(lines), i+3)
                        context = '\n'.join(lines[context_start:context_end])

                        results.append({
                            "file": "repo_map.json",
                            "line_number": i+1,
                            "code": context,
                            "score": 0.8,  # Arbitrary score
                        })

                        # Limit to 5 matches
                        if len(results) >= 5:
                            break

                return results
    except Exception as e:
        print(f"Error searching repo_map.json directly: {e}")
    return []

if __name__ == "__main__":
    # If no arguments are provided through command line, use a default example
    if len(sys.argv) == 1:
        # Use parent directory to access the full codekite project
        repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"No arguments provided, using default repository path: {repo_path}")

        # Try to set up OpenAI embedding function if available
        embed_fn = setup_openai_embed_fn()
        if embed_fn:
            print("OpenAI API key found, using semantic search capabilities")
        else:
            print("OpenAI API key not found, will fall back to keyword search")

        # Try a few different search terms that should exist in the repository
        search_terms = ["extract_symbols", "repository", "search", "code"]

        # Try each search term until we find one that works
        results = None
        for term in search_terms:
            print(f"Running search for '{term}'...")

            # Try normal semantic search first
            term_results = semantic_search(repo_path, term, 10, embed_fn)

            # If that fails, try direct repo_map.json search as a fallback
            if not term_results:
                term_results = direct_repo_map_search(repo_path, term)

            if term_results:
                search_term = term
                results = term_results
                break

        if not results:
            print("No matches found for your query.")
            sys.exit(0)

        # Use the nicer formatting function
        format_output(f"Search Results for '{search_term}'", results)

        # Additional information about improving results
        print("\nTo use true semantic search capabilities:")
        print("1. Install the OpenAI package: uv pip install openai")
        print("2. Set your OpenAI API key: export OPENAI_API_KEY='your-api-key'")
        print("3. Run the script again")
    else:
        main()

"""
Map Repository Demo

This script demonstrates how to use Kit to generate a complete map
of a repository's structure and symbols, outputting the results as JSON.

Usage:
  python map_repository.py [local_repo_path_or_github_url]
"""
import os
import sys
import json
import time
from kit import Repository

def map_repository(repo_path_or_url):
    """Map the repository and output its structure as JSON"""
    start_time = time.time()

    print(f"Initializing repository from: {repo_path_or_url}")
    # Repository handles both local paths and GitHub URLs
    repo = Repository(repo_path_or_url)

    print(f"Repository initialized in {time.time() - start_time:.2f} seconds")
    print(f"Repository info: {repo}")

    # Get the file tree
    print("\nExtracting file tree...")
    file_tree = repo.get_file_tree()

    # Extract symbols from all Python files
    print("\nExtracting symbols from Python files...")
    symbols_by_file = {}
    py_files = [f["path"] for f in file_tree if not f.get("is_dir", False) and f["path"].endswith(".py")]

    for py_file in py_files:
        print(f"  Processing {py_file}")
        try:
            symbols = repo.extract_symbols(py_file)
            symbols_by_file[py_file] = symbols
        except Exception as e:
            print(f"  Error extracting symbols from {py_file}: {str(e)}")

    # Create the complete repo map
    repo_map = {
        "repository": {
            "path": repo_path_or_url,
            "is_remote": repo_path_or_url.startswith("http"),
            "file_count": len([f for f in file_tree if not f.get("is_dir", False)]),
            "directory_count": len([f for f in file_tree if f.get("is_dir", False)]),
            "python_file_count": len(py_files)
        },
        "file_tree": [f["path"] for f in file_tree],
        "symbols": symbols_by_file
    }

    # Add dependency graph if we have Python files
    if py_files:
        try:
            print("\nAnalyzing dependencies...")
            analyzer = repo.get_dependency_analyzer()
            graph = analyzer.build_dependency_graph()

            # Add simplified dependency representation (source file → imported files)
            dependencies = {}
            for node, edges in graph.items():
                if node in py_files:
                    dependencies[node] = list(edges)

            repo_map["dependencies"] = dependencies
        except Exception as e:
            print(f"Error analyzing dependencies: {str(e)}")

    total_time = time.time() - start_time
    repo_map["metadata"] = {
        "analysis_time": total_time,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    return repo_map

if __name__ == "__main__":
    if len(sys.argv) > 1:
        repo_path_or_url = sys.argv[1]
    else:
        # Use the kit repo itself as default
        # Use parent directory to access the full codekite project
        repo_path_or_url = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Map the repository
    repo_map = map_repository(repo_path_or_url)

    # Output the JSON map
    print("\nRepository Map (JSON):")
    print(json.dumps(repo_map, indent=2))

    # Optionally save to file
    output_file = "repo_map.json"
    with open(output_file, "w") as f:
        json.dump(repo_map, f, indent=2)
    print(f"\nRepository map saved to: {output_file}")

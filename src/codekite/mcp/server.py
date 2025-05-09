#!/usr/bin/env python
"""
Simple FastMCP server for CodeKit.

This is a lightweight MCP server implementation that avoids
complex typing issues. Use this for testing and development.
"""

import asyncio
import os
import json
import re
import fnmatch
import tempfile
from datetime import datetime

from fastmcp import FastMCP

# Initialize server
mcp = FastMCP(name="CodeKit Simple MCP", on_duplicate_tools="replace", on_duplicate_resources="replace")

# Simple in-memory repository storage
_repos = {}

# Repository class definition
class Repository:
    """Simplified Repository class for MCP."""

    def __init__(self, path_or_url):
        """Initialize with path or URL."""
        self.is_remote = path_or_url.startswith(("http://", "https://"))
        self.original_path = path_or_url

        if self.is_remote:
            # Create temp directory for cloning
            self.temp_dir = tempfile.mkdtemp()
            self.path = self.temp_dir
            self._clone_repository(path_or_url)
        else:
            self.path = path_or_url
            self.temp_dir = None

    def _clone_repository(self, url):
        """Clone a git repository to the temp directory."""
        import subprocess
        try:
            subprocess.run(
                ["git", "clone", "--depth=1", url, self.path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e.stderr}")
            raise ValueError(f"Failed to clone repository: {e.stderr}")

    def __del__(self):
        """Clean up temporary directory if necessary."""
        if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def get_files(self):
        """Get files in repository."""
        files = []
        for root, _, filenames in os.walk(self.path):
            for filename in filenames:
                # Skip hidden files and directories
                if filename.startswith('.'):
                    continue
                rel_path = os.path.relpath(os.path.join(root, filename), self.path)
                files.append(rel_path)
        return files

    def get_structure(self):
        """Get repository structure."""
        return {
            "path": self.path,
            "files": self._get_file_tree(),
        }

    def _get_file_tree(self):
        """Get file tree as list of dictionaries."""
        result = []
        for root, dirs, files in os.walk(self.path):
            rel_root = os.path.relpath(root, self.path)
            if rel_root == '.':
                rel_root = ''

            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            # Add directories
            for dir_name in dirs:
                if dir_name.startswith('.'):
                    continue
                dir_path = os.path.join(rel_root, dir_name)
                result.append({
                    "path": dir_path,
                    "type": "directory",
                    "name": dir_name,
                })

            # Add files
            for file_name in files:
                if file_name.startswith('.'):
                    continue
                file_path = os.path.join(rel_root, file_name)
                result.append({
                    "path": file_path,
                    "type": "file",
                    "name": file_name,
                })

        return result

    def get_language_stats(self):
        """Get statistics about programming languages used."""
        extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".c": "C",
            ".cpp": "C++",
            ".rb": "Ruby",
            ".md": "Markdown",
            ".html": "HTML",
            ".css": "CSS",
        }

        stats = {}
        for file_path in self.get_files():
            _, ext = os.path.splitext(file_path)
            lang = extensions.get(ext, "Other")
            stats[lang] = stats.get(lang, 0) + 1

        return stats

    def get_last_updated_time(self):
        """Get last updated time."""
        return datetime.now().isoformat()

    def search_text(self, query, file_pattern="*"):
        """Search for text in repository."""
        results = []
        pattern = re.compile(query)

        for file_path in self.get_files():
            if not fnmatch.fnmatch(file_path, file_pattern):
                continue

            try:
                with open(os.path.join(self.path, file_path), 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if pattern.search(line):
                            results.append({
                                "file": file_path,
                                "line_number": i,
                                "line": line.rstrip(),
                            })
            except Exception:
                # Skip files we can't read
                continue

        return results

# Core Tools that map to API client methods

@mcp.tool()
async def codekite_open_repository(
    path_or_url,
    github_token=None,
    ctx=None
):
    """
    Open a repository and return its ID.

    Args:
        path_or_url: Repository path or URL
        github_token: Optional GitHub token for private repositories
        ctx: MCP context (injected automatically)

    Returns:
        Dictionary with ID of the opened repository
    """
    try:
        if ctx:
            await ctx.info(f"Opening repository: {path_or_url}")

        repo = Repository(path_or_url)
        repo_id = str(len(_repos) + 1)
        _repos[repo_id] = repo

        if ctx:
            await ctx.info(f"Repository opened with ID: {repo_id}")

        return {"id": repo_id}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error opening repository: {e}")
        raise

@mcp.tool()
async def codekite_search_code(
    repo_id,
    query,
    file_pattern="*.py",
    ctx=None
):
    """
    Search for text in a repository.

    Search for code matching a text or regex pattern within files
    that match the specified glob pattern.

    Args:
        repo_id: Repository ID
        query: Text or regex pattern to search for
        file_pattern: Glob pattern for files to search (default: "*.py")
        ctx: MCP context (injected automatically)

    Returns:
        List of search results with file, line number, and matching text
    """
    if repo_id not in _repos:
        if ctx:
            await ctx.error(f"Repository {repo_id} not found")
        raise ValueError(f"Repository {repo_id} not found")

    try:
        if ctx:
            await ctx.info(f"Searching for '{query}' in {file_pattern} files")

        repo = _repos[repo_id]
        results = repo.search_text(query, file_pattern=file_pattern)

        if ctx:
            await ctx.info(f"Found {len(results)} matches")

        return results
    except Exception as e:
        if ctx:
            await ctx.error(f"Error during search: {e}")
        raise

@mcp.tool()
async def codekite_build_context(
    repo_id,
    query,
    max_tokens=4000,
    ctx=None
):
    """
    Build context for LLMs from repository based on query.

    Generates a context that includes relevant code snippets, documentation and
    file structure based on the query. This is useful for getting the AI assistant
    to understand specific parts of the codebase.

    Args:
        repo_id: Repository ID
        query: Query to build context for
        max_tokens: Maximum number of tokens in context (100-8000)
        ctx: MCP context (injected automatically)

    Returns:
        Dictionary with context string
    """
    if repo_id not in _repos:
        if ctx:
            await ctx.error(f"Repository {repo_id} not found")
        raise ValueError(f"Repository {repo_id} not found")

    try:
        if ctx:
            await ctx.info(f"Building context for '{query}'")

        # Simple implementation for standalone mode - just search and format results
        repo = _repos[repo_id]
        search_results = repo.search_text(query)

        # Generate a simple context with repo structure and search results
        structure = repo.get_structure()

        context = [
            f"# Repository: {repo.path}",
            f"Query: {query}",
            "",
            "## Repository Structure",
            "```",
            json.dumps(structure, indent=2)[:500] + "...",  # Truncate to keep context manageable
            "```",
            "",
            "## Search Results",
        ]

        for result in search_results[:20]:  # Limit to 20 results
            context.append(f"\nFile: {result['file']}, Line {result['line_number']}")
            context.append(f"```python\n{result['line']}\n```")

        context_str = "\n".join(context)

        # Crude token count estimation - approx 4 chars per token
        if len(context_str) > max_tokens * 4:
            context_str = context_str[:max_tokens * 4] + "...\n[Context truncated to fit token limit]"

        if ctx:
            await ctx.info(f"Context built successfully ({len(context_str) // 4} tokens approx.)")

        return {"context": context_str}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error building context: {e}")
        raise

# Resource templates for repository information

@mcp.resource("codekite://repository/{repo_id}/structure")
async def codekite_get_repo_structure(repo_id):
    """
    Get repository structure.

    Returns a hierarchical representation of the repository's files and directories.

    Args:
        repo_id: Repository ID

    Returns:
        Repository structure as a dictionary
    """
    if repo_id not in _repos:
        raise ValueError(f"Repository {repo_id} not found")

    repo = _repos[repo_id]
    return repo.get_structure()

@mcp.resource("codekite://repository/{repo_id}/summary")
async def codekite_get_repo_summary(repo_id):
    """
    Get repository summary information.

    Returns a summary of the repository including file counts, language statistics,
    and other metadata.

    Args:
        repo_id: Repository ID

    Returns:
        Repository summary as a dictionary
    """
    if repo_id not in _repos:
        raise ValueError(f"Repository {repo_id} not found")

    repo = _repos[repo_id]
    return {
        "id": repo_id,
        "path": repo.path,
        "file_count": len(repo.get_files()),
        "language_stats": repo.get_language_stats(),
        "last_updated": repo.get_last_updated_time(),
    }

@mcp.resource("codekite://repository/{repo_id}/docstrings")
async def codekite_get_repo_docstrings(repo_id):
    """
    Get all docstrings from the repository.

    Extracts and returns all docstrings found in the repository's code files.

    Args:
        repo_id: Repository ID

    Returns:
        List of docstrings with file, function/class name, and content
    """
    if repo_id not in _repos:
        raise ValueError(f"Repository {repo_id} not found")

    # Use the repo if we implement full docstring extraction
    # For now return a placeholder
    return [
        {
            "file": "example.py",
            "name": "example_function",
            "type": "function",
            "docstring": "This is an example docstring."
        }
    ]

# Main function to run the server in standalone mode
async def main():
    """Run the MCP server in standalone mode."""
    print("[INFO] Starting Simple CodeKit MCP server...")
    await mcp.run_async(transport="streamable-http", port=8000, host="0.0.0.0", path="/mcp")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped.")

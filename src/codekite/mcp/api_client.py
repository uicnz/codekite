"""API Client for use with FastMCP tools."""
from __future__ import annotations

from typing import Dict, List, Any, Optional

from fastmcp.server.context import Context
from ..repository import Repository


class APIClient:
    """Client wrapper for codekite API functions.

    This class provides methods that will be used by the MCP tools
    to interact with the codekite functionality.
    """

    def __init__(self, repos: Dict[str, Repository]):
        """Initialize API client with repository storage."""
        self._repos = repos

    async def open_repo(self, path_or_url: str, github_token: Optional[str] = None, ctx: Optional[Context] = None) -> Dict[str, str]:
        """Open a repository and return its ID."""
        try:
            if ctx:
                await ctx.info(f"Opening repository: {path_or_url}")

            repo = Repository(path_or_url, github_token=github_token)
            repo_id = str(len(self._repos) + 1)
            self._repos[repo_id] = repo

            if ctx:
                await ctx.info(f"Repository opened with ID: {repo_id}")

            return {"id": repo_id}
        except Exception as e:
            if ctx:
                await ctx.error(f"Error opening repository: {e}")
            raise

    async def search_text(self, repo_id: str, q: str, pattern: str = "*.py", ctx: Optional[Context] = None) -> List[Dict[str, Any]]:
        """Search for text in repository."""
        if repo_id not in self._repos:
            if ctx:
                await ctx.error(f"Repository {repo_id} not found")
            raise ValueError(f"Repository {repo_id} not found")

        try:
            if ctx:
                await ctx.info(f"Searching for '{q}' in {pattern} files")

            repo = self._repos[repo_id]
            results = repo.search_text(q, file_pattern=pattern)

            if ctx:
                await ctx.info(f"Found {len(results)} matches")

            return results
        except Exception as e:
            if ctx:
                await ctx.error(f"Error during search: {e}")
            raise

    async def build_context(self, repo_id: str, query: str, max_tokens: int = 4000, ctx: Optional[Context] = None) -> Dict[str, str]:
        """Build context for LLM from repository."""
        if repo_id not in self._repos:
            if ctx:
                await ctx.error(f"Repository {repo_id} not found")
            raise ValueError(f"Repository {repo_id} not found")

        try:
            if ctx:
                await ctx.info(f"Building context for query: {query}")

            repo = self._repos[repo_id]
            assembler = repo.get_context_assembler()
            context = assembler.assemble_context(query, max_tokens=max_tokens)

            if ctx:
                await ctx.info(f"Context built successfully: {len(context)} characters")

            return {"context": context}
        except Exception as e:
            if ctx:
                await ctx.error(f"Error building context: {e}")
            raise

    async def get_repo_structure(self, repo_id: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
        """Get repository structure."""
        if repo_id not in self._repos:
            if ctx:
                await ctx.error(f"Repository {repo_id} not found")
            raise ValueError(f"Repository {repo_id} not found")

        try:
            if ctx:
                await ctx.info(f"Getting structure for repository {repo_id}")

            repo = self._repos[repo_id]
            structure = repo.get_structure()

            if ctx:
                await ctx.info("Retrieved repository structure")

            return structure
        except Exception as e:
            if ctx:
                await ctx.error(f"Error getting repository structure: {e}")
            raise

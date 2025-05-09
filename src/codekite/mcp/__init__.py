"""CodeKit MCP server implementation."""

# Define what this module exports
__all__ = ["mcp"]

# Use a more conservative approach that doesn't try to modify the module
# This avoids the circular import warning without complex module manipulation

# Define a variable that will lazily import on first access
_mcp = None

def __getattr__(name):
    """Import attributes lazily on first access."""
    global _mcp

    if name == "mcp":
        if _mcp is None:
            # Only import when actually needed
            from .server import mcp as server_mcp
            _mcp = server_mcp
        return _mcp

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

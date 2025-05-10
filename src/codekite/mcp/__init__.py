"""CodeKite MCP server implementation."""

# Define what this module exports
__all__ = ["mcp", "app", "create_app", "run_server"]

# Use a more conservative approach that doesn't try to modify the module
# This avoids the circular import warning without complex module manipulation

# Define variables that will lazily import on first access
_mcp = None
_app = None
_create_app = None
_run_server = None

def __getattr__(name):
    """Import attributes lazily on first access."""
    global _mcp, _app, _create_app, _run_server

    if name == "mcp":
        if _mcp is None:
            # Only import when actually needed
            from .server import mcp as server_mcp
            _mcp = server_mcp
        return _mcp
    elif name == "app":
        if _app is None:
            # Import the ASGI app instance
            from .asgi import app as asgi_app
            _app = asgi_app
        return _app
    elif name == "create_app":
        if _create_app is None:
            # Import the create_app function
            from .asgi import create_app as asgi_create_app
            _create_app = asgi_create_app
        return _create_app
    elif name == "run_server":
        if _run_server is None:
            # Import the run_server function
            from .asgi import run_server as asgi_run_server
            _run_server = asgi_run_server
        return _run_server

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

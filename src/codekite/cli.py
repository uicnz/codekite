
"""codekite Command Line Interface."""

import importlib.metadata
from enum import Enum
import typer

app = typer.Typer(help="A modular toolkit for LLM-powered codebase understanding.")

class MCPTransport(str, Enum):
    """MCP transport protocol options."""
    STREAMABLE_HTTP = "streamable-http"
    SSE = "sse"
    STDIO = "stdio"

def _get_version():
    """Get the package version from metadata."""
    return importlib.metadata.version("codekite")

def version_callback(value: bool):
    """Handle --version flag."""
    if value:
        typer.echo(f"codekite version: {_get_version()}")
        raise typer.Exit()
    return value

@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", help="Show the version and exit.", callback=version_callback
    ),
):
    """codekite CLI main entrypoint."""
    pass

@app.command()
def version():
    """Show the version and exit."""
    typer.echo(f"codekite version: {_get_version()}")


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """Run the codekite REST API server (requires `codekite[api]` dependencies)."""
    try:
        import uvicorn
        from codekite.api import app as fastapi_app  # Import the FastAPI app instance
    except ImportError:
        typer.secho(
            "Error: FastAPI or Uvicorn not installed. Please run `pip install codekite[api]`",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    typer.echo(f"Starting codekite API server on http://{host}:{port}")
    # When reload=True, we must use import string instead of app instance
    if reload:
        uvicorn.run("codekite.api.app:app", host=host, port=port, reload=reload)
    else:
        uvicorn.run(fastapi_app, host=host, port=port, reload=reload)


@app.command()
def search(
    path: str = typer.Argument(..., help="Path to the local repository."),
    query: str = typer.Argument(..., help="Text or regex pattern to search for."),
    pattern: str = typer.Option("*.py", "--pattern", "-p", help="Glob pattern for files to search."),
):
    """Perform a textual search in a local repository."""
    from codekite import Repository  # Local import to avoid circular deps if CLI is imported elsewhere

    try:
        repo = Repository(path)
        results = repo.search_text(query, file_pattern=pattern)
        if results:
            for res in results:
                typer.echo(f"{res['file']}:{res['line_number']}: {res['line'].strip()}")
        else:
            typer.echo("No results found.")
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def mcp_serve(
    transport: MCPTransport = typer.Option(
        MCPTransport.STREAMABLE_HTTP, "--transport", "-t",
        help="MCP transport protocol to use"
    ),
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind server"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind server"),
    mcp_path: str = typer.Option("/mcp", "--path", help="Path for MCP endpoint (for HTTP transports)"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
    use_asgi: bool = typer.Option(True, "--asgi/--simple", help="Use ASGI-compatible server (recommended)"),
    log_level: str = typer.Option("info", "--log-level", help="Log level (debug, info, warning, error)"),
):
    """Run the codekite MCP server with configurable transport protocols."""
    try:
        # Check if FastMCP is available without importing it
        import importlib.util
        if importlib.util.find_spec("fastmcp") is None:
            raise ImportError("FastMCP is not installed")

        # Check for required packages
        if importlib.util.find_spec("starlette") is None and use_asgi:
            raise ImportError("Starlette is not installed but required for ASGI mode")

        if importlib.util.find_spec("uvicorn") is None and transport != MCPTransport.STDIO:
            raise ImportError("Uvicorn is not installed but required for HTTP transports")

    except ImportError as e:
        typer.secho(
            f"Error: {e}. Please run `uv add fastmcp uvicorn starlette`",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    # For STDIO transport, always use the simple mode
    if transport == MCPTransport.STDIO:
        use_asgi = False
        typer.echo("Starting CodeKite MCP server with STDIO transport")

        try:
            from codekite.mcp import mcp
            mcp.run(transport="stdio")
        except ImportError as e:
            typer.secho(
                f"Error importing MCP module from codekite: {e}",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)
        return

    # For HTTP transports (Streamable HTTP or SSE)
    transport_str = transport.value  # Convert enum to string

    if use_asgi:
        # Use the new ASGI implementation
        try:
            import uvicorn
            import asyncio
            from codekite.mcp.asgi import app, run_server

            # Print server info
            if transport == MCPTransport.STREAMABLE_HTTP:
                typer.echo(f"Starting CodeKite MCP server (ASGI) with Streamable HTTP transport on http://{host}:{port}{mcp_path}")
            elif transport == MCPTransport.SSE:
                typer.echo(f"Starting CodeKite MCP server (ASGI) with SSE transport on http://{host}:{port}")

            # Handle reload case using uvicorn directly
            if reload:
                uvicorn.run(
                    "codekite.mcp.asgi:app",
                    host=host,
                    port=port,
                    reload=True,
                    log_level=log_level
                )
            else:
                # Use our run_server function for non-reload mode
                asyncio.run(run_server(host=host, port=port, log_level=log_level))

        except ImportError as e:
            typer.secho(
                f"Error importing ASGI module from codekite: {e}",
                fg=typer.colors.RED,
            )
            typer.secho(
                "This might be due to a missing dependency or an error in the MCP implementation.",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=1)
    else:
        # Use the simple implementation
        try:
            from codekite.mcp import mcp

            # Print server info
            if transport == MCPTransport.STREAMABLE_HTTP:
                typer.echo(f"Starting CodeKite MCP server (Simple) with Streamable HTTP transport on http://{host}:{port}{mcp_path}")
            elif transport == MCPTransport.SSE:
                typer.echo(f"Starting CodeKite MCP server (Simple) with SSE transport on http://{host}:{port}")

            # Configure settings
            config = {
                "host": host,
                "port": port,
            }

            if transport == MCPTransport.STREAMABLE_HTTP:
                config["path"] = mcp_path

            # Configure CORS for development
            config["cors_origins"] = ["*"]

            # Run FastMCP with the appropriate transport
            mcp.run(transport=transport_str, **config)

        except ImportError as e:
            typer.secho(
                f"Error importing MCP module from codekite: {e}",
                fg=typer.colors.RED,
            )
            typer.secho(
                "This might be due to a missing dependency or an error in the MCP implementation.",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

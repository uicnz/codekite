"""codekite Command Line Interface."""

import importlib.metadata
import typer

app = typer.Typer(help="A modular toolkit for LLM-powered codebase understanding.")

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


if __name__ == "__main__":
    app()

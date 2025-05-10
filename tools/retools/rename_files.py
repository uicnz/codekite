"""Rename files and directories containing specified terms."""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from re import Pattern

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

# Configuration constants
# Terms to search for
SEARCH_TERMS = [
    "langflow",
    "Langflow",
    "LANGFLOW"
]

# Terms to replace with (matching case)
REPLACE_TERMS = [
    "warpflow",
    "Warpflow",
    "WARPFLOW"
]

FROM_NAME = "Langflow"  # Original name (for display purposes)
TO_NAME = "Warpflow"    # New name (for display purposes)

# Directories to exclude from processing - EXACT paths only
EXCLUDE_DIRS = {
    ".git",  # Only exclude git internals, not .github
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "tools"  # Exclude entire tools directory
}

# Important directories to INCLUDE even if they start with a dot
INCLUDE_DOT_DIRS = {
    ".github",
    ".devcontainer"
}

# Function to check if a path is in the excluded dirs (exact path matching only)
def is_excluded_dir(path: str) -> bool:
    """Check if a path is in the excluded directories list.

    Only excludes exact matches to prevent excluding directories that just contain
    the name as part of their path (e.g., src/backend/tests/components/tools/).
    """
    path_obj = Path(path).resolve()
    for exclude in EXCLUDE_DIRS:
        exclude_path = Path(exclude).resolve()
        # Only exclude if it's the exact directory or a direct subdirectory
        if (str(path_obj) == str(exclude_path) or
                (Path(exclude).name == path_obj.name and exclude_path in path_obj.parents)):
            return True
    return False

# Exclude our scripts
EXCLUDE_FILES = {
    "find_names.py",
    "find_content.py",
    "replace_content.py",
    "rename_files.py"
}

console = Console()
# Write log files to the tools directory
TOOLS_DIR = Path(__file__).parent.absolute()
LOG_FILE = TOOLS_DIR / f"file_renames_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"


def create_search_pattern(terms: list[str]) -> Pattern:
    """Create a case-insensitive regex pattern from the list of terms."""
    pattern_str = "|".join(re.escape(term) for term in terms)
    return re.compile(pattern_str, re.IGNORECASE)


def find_matching_names(root_dir: str = ".") -> tuple[list[str], list[str]]:
    """Find files and directories with any of the search terms in their names."""
    files_with_matches = []
    dirs_with_matches = []
    pattern = create_search_pattern(SEARCH_TERMS)

    with Progress(
        SpinnerColumn(),
        TextColumn(f"[bold blue]Scanning for {FROM_NAME} references in file/directory names..."),
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning", total=None)

        for root, dirs, files in os.walk(root_dir, topdown=True):
            # Improved directory exclusion logic
            # Only exclude dot directories that are not in the INCLUDE_DOT_DIRS list
            dirs[:] = [d for d in dirs if (not is_excluded_dir(Path(root) / d) and
                                          (not d.startswith(".") or d in INCLUDE_DOT_DIRS))]

            # Check directories
            for d in dirs:
                if pattern.search(d):
                    full_path = Path(root) / d
                    dirs_with_matches.append(str(full_path))

            # Check files
            for f in files:
                if f in EXCLUDE_FILES:
                    continue
                if pattern.search(f):
                    full_path = Path(root) / f
                    files_with_matches.append(str(full_path))

            progress.update(task)

    return dirs_with_matches, files_with_matches


def generate_new_name(original_name: str) -> str:
    """Generate a new name by replacing occurrences of the search terms."""
    new_name = original_name

    # Perform case-sensitive replacements for each pattern
    for i, search_term in enumerate(SEARCH_TERMS):
        replace_term = REPLACE_TERMS[i] if i < len(REPLACE_TERMS) else REPLACE_TERMS[0]
        new_name = new_name.replace(search_term, replace_term)

    return new_name


def display_rename_plan(dirs_to_rename: list[str], files_to_rename: list[str]) -> None:
    """Display the rename plan in a structured format."""
    # Create a summary table
    summary_table = Table(show_header=False, box=box.ROUNDED)
    summary_table.add_column("Item", style="cyan")
    summary_table.add_column("Count", style="green")
    summary_table.add_row("Directories to rename", str(len(dirs_to_rename)))
    summary_table.add_row("Files to rename", str(len(files_to_rename)))

    console.print(Panel(summary_table, title="[bold]Rename Summary", border_style="blue"))

    # Display directories to rename
    if dirs_to_rename:
        console.print("\n[bold cyan]Directories to Rename[/bold cyan]")
        dir_table = Table(box=box.SIMPLE)
        dir_table.add_column("Current Path", style="yellow")
        dir_table.add_column("New Path", style="green")

        for d in sorted(dirs_to_rename):
            path_obj = Path(d)
            parent = path_obj.parent
            new_name = generate_new_name(path_obj.name)
            new_path = parent / new_name
            dir_table.add_row(str(path_obj), str(new_path))

        console.print(dir_table)

    # Display files to rename
    if files_to_rename:
        console.print("\n[bold cyan]Files to Rename[/bold cyan]")
        file_table = Table(box=box.SIMPLE)
        file_table.add_column("Current Path", style="yellow")
        file_table.add_column("New Path", style="green")

        for f in sorted(files_to_rename):
            path_obj = Path(f)
            parent = path_obj.parent
            new_name = generate_new_name(path_obj.name)
            new_path = parent / new_name
            file_table.add_row(str(path_obj), str(new_path))

        console.print(file_table)


def rename_items(
    dirs_to_rename: list[str],
    files_to_rename: list[str],
    *,
    dry_run: bool = True
) -> tuple[list[str], list[str]]:
    """Rename files and directories containing the search terms.

    If dry_run is True, only show what would be changed without making actual changes.
    Returns lists of successfully renamed directories and files.
    """
    renamed_dirs = []
    renamed_files = []

    # Open a log file for detailed output
    with Path(LOG_FILE).open("w") as log:
        log.write(f"File/Directory Renaming: {FROM_NAME} -> {TO_NAME}\n")
        # Format the timestamp in a more manageable way
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"{'DRY RUN - ' if dry_run else ''}Started at: {timestamp}\n")
        log.write("=" * 80 + "\n\n")

        # Log the planned renames
        log.write("PLANNED RENAMES:\n")
        log.write(f"Directories to rename: {len(dirs_to_rename)}\n")

        if dirs_to_rename:
            log.write("\nDirectories:\n")
            for d in sorted(dirs_to_rename):
                path_obj = Path(d)
                parent = path_obj.parent
                new_name = generate_new_name(path_obj.name)
                new_path = parent / new_name
                log.write(f"  {d} -> {new_path}\n")

        log.write(f"\nFiles to rename: {len(files_to_rename)}\n")
        if files_to_rename:
            log.write("\nFiles:\n")
            for f in sorted(files_to_rename):
                path_obj = Path(f)
                parent = path_obj.parent
                new_name = generate_new_name(path_obj.name)
                new_path = parent / new_name
                log.write(f"  {f} -> {new_path}\n")

        log.write("\n" + "=" * 80 + "\n\n")

        if not dry_run:
            log.write("RENAME OPERATIONS:\n\n")

            # Rename files first
            log.write("RENAMING FILES:\n")
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Renaming files..."),
                transient=True,
            ) as progress:
                task = progress.add_task("Renaming", total=len(files_to_rename))

                for f in sorted(files_to_rename):
                    try:
                        path_obj = Path(f)
                        parent = path_obj.parent
                        new_name = generate_new_name(path_obj.name)
                        new_path = parent / new_name

                        # Rename the file (Git will track the changes)
                        log.write(f"Renaming file: {path_obj} -> {new_path}\n")
                        path_obj.rename(new_path)
                        renamed_files.append((str(path_obj), str(new_path)))
                        log.write("[SUCCESS]\n")

                    except (FileNotFoundError, PermissionError, OSError) as e:
                        # Handle common file system errors specifically
                        error_msg = f"File system error renaming file {f}: {e!s}"
                        console.print(f"[red]{error_msg}[/red]")
                        log.write(f"[ERROR] {error_msg}\n")
                    except Exception as e:  # noqa: BLE001
                        # Fallback for unexpected errors to prevent script from crashing
                        # We catch all exceptions here to prevent batch operations from failing completely
                        error_msg = f"Unexpected error renaming file {f}: {e!s}"
                        console.print(f"[red]{error_msg}[/red]")
                        console.print("[yellow]Please report this error with the details above.[/yellow]")
                        log.write(f"[ERROR] {error_msg}\n")

                    progress.update(task, advance=1)

            log.write("\n")

            # Rename directories in reverse order (bottom-up)
            log.write("RENAMING DIRECTORIES:\n")
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Renaming directories..."),
                transient=True,
            ) as progress:
                # Sort directories in reverse order to handle nested directories correctly
                dirs_sorted = sorted(dirs_to_rename, reverse=True)
                task = progress.add_task("Renaming", total=len(dirs_sorted))

                for d in dirs_sorted:
                    try:
                        path_obj = Path(d)
                        parent = path_obj.parent
                        new_name = generate_new_name(path_obj.name)
                        new_path = parent / new_name

                        # Rename the directory
                        log.write(f"Renaming directory: {path_obj} -> {new_path}\n")
                        path_obj.rename(new_path)
                        renamed_dirs.append((str(path_obj), str(new_path)))
                        log.write("[SUCCESS]\n")

                    except (FileNotFoundError, PermissionError, OSError) as e:
                        # Handle common file system errors specifically
                        error_msg = f"File system error renaming directory {d}: {e!s}"
                        console.print(f"[red]{error_msg}[/red]")
                        log.write(f"[ERROR] {error_msg}\n")
                    except Exception as e:  # noqa: BLE001
                        # Fallback for unexpected errors to prevent script from crashing
                        # We catch all exceptions here to prevent batch operations from failing completely
                        error_msg = f"Unexpected error renaming directory {d}: {e!s}"
                        console.print(f"[red]{error_msg}[/red]")
                        console.print("[yellow]Please report this error with the details above.[/yellow]")
                        log.write(f"[ERROR] {error_msg}\n")

                    progress.update(task, advance=1)

            # Write the final statistics to the log
            log.write("\n\n")
            log.write("=" * 80 + "\n")
            log.write("RENAMING RESULTS SUMMARY:\n")
            log.write(f"Files successfully renamed: {len(renamed_files)} of {len(files_to_rename)}\n")
            log.write(f"Directories successfully renamed: {len(renamed_dirs)} of {len(dirs_to_rename)}\n")
            log.write("=" * 80 + "\n")

        # Format completion timestamp
        end_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"\nOperation {'completed' if not dry_run else 'would complete'} at: {end_time}\n")
        if dry_run:
            log.write("NO RENAMES WERE PERFORMED - THIS WAS A DRY RUN\n")

    return renamed_dirs, renamed_files


def main():
    """Run the main program."""
    console.print(
        Panel.fit(
            f"[bold cyan]{FROM_NAME} to {TO_NAME} File/Directory Renaming (Bulletproof Edition)[/bold cyan]",
            border_style="cyan",
        )
    )

    console.print("[yellow]Using improved directory exclusion logic to catch all references[/yellow]")

    # Find files and directories to rename
    dirs_to_rename, files_to_rename = find_matching_names()

    if not dirs_to_rename and not files_to_rename:
        console.print(f"\n[yellow]No files or directories with '{FROM_NAME}' in their names found.[/yellow]")
        return

    # Display the rename plan
    display_rename_plan(dirs_to_rename, files_to_rename)

    # Ask for confirmation before making changes
    if Confirm.ask(f"\nProceed with renaming {len(files_to_rename)} files and {len(dirs_to_rename)} directories?"):
        # Perform the actual renaming
        renamed_dirs, renamed_files = rename_items(dirs_to_rename, files_to_rename, dry_run=False)

        # Report results
        console.print("\n[bold green]Rename Operation Complete![/bold green]")
        console.print(f"Successfully renamed {len(renamed_files)} files and {len(renamed_dirs)} directories.")

        if len(renamed_dirs) < len(dirs_to_rename) or len(renamed_files) < len(files_to_rename):
            console.print("\n[yellow]Note: Some items could not be renamed. Check the errors above.[/yellow]")
    else:
        console.print("\n[yellow]Operation cancelled. No files or directories were renamed.[/yellow]")


if __name__ == "__main__":
    main()

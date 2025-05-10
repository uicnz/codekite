"""Find files and directories with specified terms in their names, with rich formatted output."""

import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

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
LOG_FILE = TOOLS_DIR / f"name_references_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"


def create_search_pattern(terms: list[str]) -> re.Pattern:
    """Create a case-insensitive regex pattern from the list of terms."""
    pattern_str = "|".join(re.escape(term) for term in terms)
    return re.compile(pattern_str, re.IGNORECASE)


def find_matching_names(root_dir: str = ".") -> tuple[list[str], list[str]]:
    """Find files and directories with any of the search terms in their names."""
    files_with_matches = []
    dirs_with_matches = []
    pattern = create_search_pattern(SEARCH_TERMS)

    # Open a log file for detailed output
    with Path(LOG_FILE).open("w") as log:
        log.write(f"File/Directory Name Reference Search: {FROM_NAME} -> {TO_NAME}\n")
        log.write(f"Search started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write("=" * 80 + "\n\n")

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
                        # Log the matched directory
                        log.write(f"Directory: {full_path}\n")
                        # Note how the name would change
                        new_name = full_path.name
                        for i, search_term in enumerate(SEARCH_TERMS):
                            replace_term = REPLACE_TERMS[i] if i < len(REPLACE_TERMS) else REPLACE_TERMS[0]
                            new_name = new_name.replace(search_term, replace_term)
                        log.write(f"  Would rename to: {full_path.parent / new_name}\n")
                        log.write("-" * 60 + "\n")

                # Check files
                for f in files:
                    if f in EXCLUDE_FILES:
                        continue
                    if pattern.search(f):
                        full_path = Path(root) / f
                        files_with_matches.append(str(full_path))
                        # Log the matched file
                        log.write(f"File: {full_path}\n")
                        # Note how the name would change
                        new_name = full_path.name
                        for i, search_term in enumerate(SEARCH_TERMS):
                            replace_term = REPLACE_TERMS[i] if i < len(REPLACE_TERMS) else REPLACE_TERMS[0]
                            new_name = new_name.replace(search_term, replace_term)
                        log.write(f"  Would rename to: {full_path.parent / new_name}\n")
                        log.write("-" * 60 + "\n")

                progress.update(task)

        # Write the final statistics to the log
        log.write("\n\n")
        log.write("=" * 80 + "\n")
        log.write("SEARCH RESULTS SUMMARY:\n")
        log.write(f"Directories with '{FROM_NAME}' references: {len(dirs_with_matches)}\n")
        log.write(f"Files with '{FROM_NAME}' references: {len(files_with_matches)}\n")
        log.write("=" * 80 + "\n")
        log.write(f"Search completed at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n")

    return dirs_with_matches, files_with_matches


def group_by_directory(paths):
    """Group paths by their parent directory for cleaner output."""
    grouped = defaultdict(list)
    for path in paths:
        path_obj = Path(path)
        parent_dir = str(path_obj.parent)
        filename = path_obj.name
        grouped[parent_dir].append(filename)
    return grouped


def main():
    """Run the main program."""
    console.print(
        Panel.fit(
            f"[bold cyan]{FROM_NAME} to {TO_NAME} Refactoring Analysis (Bulletproof Edition)[/bold cyan]",
            border_style="cyan",
        )
    )

    console.print("[yellow]Using improved directory exclusion logic to catch all references[/yellow]")

    dirs_with_matches, files_with_matches = find_matching_names()

    # Print summary stats
    summary_table = Table(show_header=False, box=box.ROUNDED)
    summary_table.add_column("Item", style="cyan")
    summary_table.add_column("Count", style="green")
    summary_table.add_row(f"Directories with '{FROM_NAME}' references", str(len(dirs_with_matches)))
    summary_table.add_row(f"Files with '{FROM_NAME}' references", str(len(files_with_matches)))

    console.print(Panel(summary_table, title="[bold]Summary", border_style="blue"))

    # Print directories
    if dirs_with_matches:
        console.print("\n[bold cyan]Directories[/bold cyan]")
        dir_tree = Tree("📁 [bold]Project Root[/bold]")
        for d in sorted(dirs_with_matches):
            dir_tree.add(f"[yellow]{d}[/yellow]")
        console.print(dir_tree)

    # Print files by directory
    if files_with_matches:
        console.print("\n[bold cyan]Files (grouped by directory)[/bold cyan]")
        file_tree = Tree("📁 [bold]Project Root[/bold]")
        grouped_files = group_by_directory(files_with_matches)

        for parent_dir, filenames in sorted(grouped_files.items()):
            branch = file_tree.add(f"[blue]{parent_dir}/[/blue]")
            for filename in sorted(filenames):
                branch.add(f"[green]{filename}[/green]")

        console.print(file_tree)


if __name__ == "__main__":
    main()

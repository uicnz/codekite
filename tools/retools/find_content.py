"""Find occurrences of specified terms in file contents, with rich formatted output."""

import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from re import Pattern  # Properly import from re instead of typing

from rich import box
from rich.console import Console
from rich.markup import escape
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

FROM_NAME = "Langflow"  # Original name (for display purposes)
TO_NAME = "warpflow"    # New name (for display purposes)

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

# File extensions to exclude
EXCLUDE_FILE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    # ".svg", # SVG files must be included
    ".woff",
    ".ttf",
    ".eot"
}
MAX_LINE_LENGTH = 100
MAX_PREVIEW_LENGTH = 97
MAX_FILE_SIZE = 1_000_000  # 1MB
MAX_RESULTS_PER_FILE = 5
MAX_SAMPLE_FILES = 10

console = Console()
# Write log files to the tools directory
TOOLS_DIR = Path(__file__).parent.absolute()
LOG_FILE = TOOLS_DIR / f"content_references_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"


def create_search_pattern(terms: list[str]) -> Pattern:
    """Create a case-insensitive regex pattern from the list of terms."""
    pattern_str = "|".join(re.escape(term) for term in terms)
    return re.compile(pattern_str, re.IGNORECASE)


def find_content_matches(
    root_dir: str = ".", max_results_per_file: int = MAX_RESULTS_PER_FILE
) -> tuple[dict[str, list[tuple[int, str]]], int]:
    """Find occurrences of any search terms in file contents."""
    results = defaultdict(list)
    count = 0
    pattern = create_search_pattern(SEARCH_TERMS)

    # Open a log file for detailed output
    with Path(LOG_FILE).open("w") as log:
        log.write(f"Content Reference Search: {FROM_NAME} -> {TO_NAME}\n")
        log.write(f"Search started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write("=" * 80 + "\n\n")

        with Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]Scanning for {FROM_NAME} references in file contents..."),
            transient=True,
        ) as progress:
            task = progress.add_task("Scanning", total=None)

            for root, dirs, files in os.walk(root_dir, topdown=True):
                # Improved directory exclusion logic
                # Only exclude dot directories that are not in the INCLUDE_DOT_DIRS list
                dirs[:] = [d for d in dirs if (not is_excluded_dir(Path(root) / d) and
                                              (not d.startswith(".") or d in INCLUDE_DOT_DIRS))]

                for file in files:
                    if file in EXCLUDE_FILES or any(file.endswith(ext) for ext in EXCLUDE_FILE_EXTENSIONS):
                        continue

                    # Skip large files and binary files
                    filepath = Path(root) / file
                    file_path_str = str(filepath)
                    try:
                        if filepath.stat().st_size > MAX_FILE_SIZE:
                            continue

                        with filepath.open(errors="ignore") as f:
                            try:
                                file_matches = 0
                                lines = f.readlines()
                                for line_num, line in enumerate(lines, 1):
                                    if pattern.search(line):
                                        # Only store up to max_results_per_file per file
                                        if file_matches < max_results_per_file:
                                            clean_line = line.strip()
                                            if len(clean_line) > MAX_LINE_LENGTH:
                                                clean_line = clean_line[:MAX_PREVIEW_LENGTH] + "..."
                                            results[file_path_str].append((line_num, clean_line))

                                            # Log to file
                                            log.write(f"File: {file_path_str}\n")
                                            log.write(f"Line {line_num}: {clean_line}\n")
                                            log.write("-" * 60 + "\n\n")

                                        file_matches += 1
                                        count += 1

                                # Log summary for this file if matches found
                                if file_matches > 0:
                                    log.write(f"Summary: {file_path_str} contains {file_matches} references\n")
                                    log.write("=" * 60 + "\n\n")

                            except UnicodeDecodeError:
                                # Skip binary files
                                continue
                    except (PermissionError, OSError):
                        # Skip files we can't access
                        continue

                progress.update(task)

        # Write the final statistics to the log
        log.write("\n\n")
        log.write("=" * 80 + "\n")
        log.write("SEARCH RESULTS SUMMARY:\n")
        log.write(f"Total references found: {count}\n")
        log.write(f"Files containing references: {len(results)}\n")
        log.write("=" * 80 + "\n")
        log.write(f"Search completed at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n")

    return results, count


def main():
    """Run the main program."""
    console.print(
        Panel.fit(
            f"[bold cyan]{FROM_NAME} to {TO_NAME} Content Refactoring Analysis (Bulletproof Edition)[/bold cyan]",
            border_style="cyan",
        )
    )

    console.print("[yellow]Using improved directory exclusion logic to catch all references[/yellow]")

    # Find occurrences
    results, total_count = find_content_matches()

    # Print summary
    summary_table = Table(show_header=False, box=box.ROUNDED)
    summary_table.add_column("Item", style="cyan")
    summary_table.add_column("Count", style="green")
    summary_table.add_row(f"Total '{FROM_NAME}' references", str(total_count))
    summary_table.add_row(f"Files containing '{FROM_NAME}' references", str(len(results)))

    console.print(Panel(summary_table, title="[bold]Summary", border_style="blue"))

    # Group by file extension
    extensions = defaultdict(int)
    for filepath in results:
        path_obj = Path(filepath)
        ext = path_obj.suffix.lower() or "(no extension)"
        extensions[ext] += len(results[filepath])

    # Print extension breakdown
    ext_table = Table(title="Occurrences by File Type", box=box.SIMPLE)
    ext_table.add_column("Extension", style="cyan")
    ext_table.add_column("Count", style="green", justify="right")
    ext_table.add_column("Percentage", style="yellow", justify="right")

    for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_count) * 100
        ext_table.add_row(ext, str(count), f"{percentage:.1f}%")

    console.print(ext_table)

    # Show file tree with occurrence counts
    console.print(f"\n[bold cyan]Files with '{FROM_NAME}' occurrences[/bold cyan]")
    grouped_by_dir = defaultdict(list)

    for filepath, matches in results.items():
        path_obj = Path(filepath)
        dirname = str(path_obj.parent)
        filename = path_obj.name
        grouped_by_dir[dirname].append((filename, len(matches)))

    file_tree = Tree("📁 [bold]Project Root[/bold]")

    for dirname, files in sorted(grouped_by_dir.items()):
        branch = file_tree if not dirname else file_tree.add(f"[blue]{dirname}/[/blue]")

        for filename, count in sorted(files, key=lambda x: x[1], reverse=True):
            branch.add(f"[green]{filename}[/green] ([yellow]{count}[/yellow])")

    console.print(file_tree)

    # Print sample contents
    console.print(f"\n[bold cyan]Sample Occurrences[/bold cyan] (max {MAX_RESULTS_PER_FILE} per file)")
    for filepath, matches in sorted(results.items(), key=lambda x: len(x[1]), reverse=True)[:MAX_SAMPLE_FILES]:
        console.print(f"\n[bold blue]{filepath}[/bold blue]")
        for line_num, line in matches:
            console.print(f"  Line {line_num}: [yellow]{escape(line)}[/yellow]")


if __name__ == "__main__":
    main()

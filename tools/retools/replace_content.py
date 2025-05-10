"""Replace occurrences of specified terms in file contents, with rich formatted output."""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from re import Pattern

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

# Configuration constants
# Terms to search for (expanded to cover more case variations)
SEARCH_TERMS = [
    "langflow",
    "Langflow",
    "LangFlow",  # Added: CamelCase variation
    "LANGFLOW",
    "lang_flow",  # Added: underscore variation
    "Lang_Flow", # Added: underscore with capital
    "LANG_FLOW"  # Added: uppercase with underscore
]

# Terms to replace with (matching case)
REPLACE_TERMS = [
    "warpflow",
    "Warpflow",
    "WarpFlow",  # Added: matching case for CamelCase
    "WARPFLOW",
    "warp_flow",  # Added: matching underscore variation
    "Warp_Flow", # Added: matching underscore with capital
    "WARP_FLOW"  # Added: matching uppercase with underscore
]

# Special regex patterns for imports and other critical patterns
IMPORT_PATTERNS = [
    (r"from\s+langflow(\.|$)", r"from warpflow\1"),
    (r"import\s+langflow(\.|$)", r"import warpflow\1")
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
MAX_FILE_SIZE = 1_000_000  # 1MB
MAX_REPLACEMENTS_TO_SHOW = 10  # Maximum number of replacements to show in the sample output

console = Console()
# Write log files to the tools directory
TOOLS_DIR = Path(__file__).parent.absolute()
LOG_FILE = TOOLS_DIR / f"content_replacements_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"


def create_search_patterns() -> list[tuple[Pattern, str]]:
    """Create search patterns and their replacements, maintaining case sensitivity."""
    patterns = []

    # Create search/replacement pairs from the constants
    for i, search_term in enumerate(SEARCH_TERMS):
        replace_term = REPLACE_TERMS[i] if i < len(REPLACE_TERMS) else REPLACE_TERMS[0]
        patterns.append((re.compile(re.escape(search_term)), replace_term))

    return patterns


def replace_content(
    root_dir: str = ".",
    *,
    dry_run: bool = True,
    apply_special_patterns: bool = True,
    verbose: bool = False
) -> tuple[dict[str, int], list]:
    """Replace occurrences of the specified terms in file contents.

    If dry_run is True, only show what would be changed without making actual changes.
    Returns a tuple containing:
    - Dictionary of file paths and the number of replacements made
    - List of sample replacements
    """
    patterns = create_search_patterns()
    replacements_count = {}
    sample_replacements = []

    # Open a log file for detailed output
    with Path(LOG_FILE).open("w") as log:
        log.write(f"Content Replacement: {FROM_NAME} -> {TO_NAME}\n")
        # Format the timestamp in a more manageable way
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"{'DRY RUN - ' if dry_run else ''}Started at: {timestamp}\n")
        log.write("=" * 80 + "\n\n")

        # Create progress message with operation type
        operation_type = "Analyzing" if dry_run else "Replacing"
        progress_msg = f"[bold blue]{operation_type} {FROM_NAME} references in file contents..."

        with Progress(
            SpinnerColumn(),
            TextColumn(progress_msg),
            transient=True,
        ) as progress:
            task = progress.add_task("Processing", total=None)

            for root, dirs, files in os.walk(root_dir, topdown=True):
                # Improved directory exclusion logic
                # Only exclude dot directories that are not in the INCLUDE_DOT_DIRS list
                dirs[:] = [d for d in dirs if (not is_excluded_dir(Path(root) / d) and
                                              (not d.startswith(".") or d in INCLUDE_DOT_DIRS))]

                # Debug logging for directory traversal if verbose is enabled
                if verbose:
                    log.write(f"Entering directory: {root}\n")
                    log.write(f"  Subdirectories: {', '.join(dirs)}\n")
                    log.write(f"  Files count: {len(files)}\n")

                for file in files:
                    if file in EXCLUDE_FILES or any(file.endswith(ext) for ext in EXCLUDE_FILE_EXTENSIONS):
                        continue

                    # Skip large files and binary files
                    filepath = Path(root) / file
                    file_path_str = str(filepath)
                    try:
                        if filepath.stat().st_size > MAX_FILE_SIZE:
                            continue

                        # First read the file without making changes
                        try:
                            with filepath.open("r", errors="ignore") as f:
                                content = f.read()
                        except UnicodeDecodeError:
                            # Skip binary files
                            continue
                        except (PermissionError, OSError):
                            # Skip files we can't access
                            continue

                        # Check if any patterns match
                        new_content = content
                        file_replacements = 0

                        # Log file header if we find matches
                        file_has_matches = False

                        # First apply the standard case-preserving replacements
                        for pattern, replacement in patterns:
                            # Count matches before replacement
                            matches = pattern.findall(new_content)
                            match_count = len(matches)

                            if match_count > 0:
                                # Log the file information if this is the first match in this file
                                if not file_has_matches:
                                    log.write(f"File: {file_path_str}\n")
                                    file_has_matches = True

                                # Perform the replacement
                                new_content = pattern.sub(replacement, new_content)
                                file_replacements += match_count

                                # Log each replacement type
                                log.write(
                                    f"  - Replaced {match_count} occurrences of "
                                    f"'{pattern.pattern}' with '{replacement}'\n"
                                )

                                # Save a sample for display (up to 3 examples per file)
                                if len(sample_replacements) < MAX_REPLACEMENTS_TO_SHOW and matches:
                                    for match in matches[:3]:
                                        replaced = pattern.sub(replacement, match)
                                        sample_replacements.append(
                                            (file_path_str, match, replaced, "Standard")
                                        )

                                        # Log sample replacements
                                        log.write(f"    Sample: '{match}' -> '{replaced}'\n")

                        # Apply special patterns for import statements and other code patterns
                        if apply_special_patterns and file_path_str.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                            for pattern_str, replacement_str in IMPORT_PATTERNS:
                                pattern = re.compile(pattern_str)
                                matches = pattern.findall(new_content)
                                match_count = len(matches)

                                if match_count > 0:
                                    # Log the file information if this is the first match in this file
                                    if not file_has_matches:
                                        log.write(f"File: {file_path_str}\n")
                                        file_has_matches = True

                                    # Perform the replacement
                                    new_content = pattern.sub(replacement_str, new_content)
                                    file_replacements += match_count

                                    # Log each special pattern replacement
                                    log.write(
                                        f"  - [SPECIAL] Replaced {match_count} occurrences of "
                                        f"pattern '{pattern_str}' with '{replacement_str}'\n"
                                    )

                                    # Save a sample for special patterns
                                    if len(sample_replacements) < MAX_REPLACEMENTS_TO_SHOW and matches:
                                        sample_replacements.append(
                                            (file_path_str, pattern_str, replacement_str, "Import Pattern")
                                        )

                        # Only write the file if changes were made and it's not a dry run
                        if file_replacements > 0:
                            replacements_count[file_path_str] = file_replacements

                            # Log total replacements for this file
                            log.write(f"  Total replacements in file: {file_replacements}\n")
                            log.write("-" * 60 + "\n\n")

                            if not dry_run:
                                # Write changes directly (Git will track the changes)
                                with filepath.open("w", encoding="utf-8", errors="ignore") as f:
                                    f.write(new_content)
                                log.write(f"Changes applied to {file_path_str}\n\n")

                    except (FileNotFoundError, PermissionError, OSError) as e:
                        # Handle common file system errors specifically
                        console.print(f"[red]File system error processing {filepath}: {e!s}[/red]")
                        log.write(f"ERROR: File system error processing {filepath}: {e!s}\n")
                    except Exception as e:  # noqa: BLE001
                        # Fallback for unexpected errors to prevent script from crashing
                        # We catch all exceptions here to prevent batch operations from failing completely
                        console.print(f"[red]Unexpected error processing {filepath}: {e!s}[/red]")
                        console.print("[yellow]Please report this error with the details above.[/yellow]")
                        log.write(f"ERROR: Unexpected error processing {filepath}: {e!s}\n")

                progress.update(task)

        # Write the final statistics to the log
        log.write("\n\n")
        log.write("=" * 80 + "\n")
        log.write("REPLACEMENT RESULTS SUMMARY:\n")
        log.write(f"Total replacements made: {sum(replacements_count.values())}\n")
        log.write(f"Files modified: {len(replacements_count)}\n")
        log.write("=" * 80 + "\n")
        # Format completion timestamp
        end_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"Operation {'completed' if not dry_run else 'would complete'} at: {end_time}\n")
        if dry_run:
            log.write("NO CHANGES WERE MADE - THIS WAS A DRY RUN\n")

    return replacements_count, sample_replacements


def main():
    """Run the main program."""
    console.print(
        Panel.fit(
            f"[bold cyan]{FROM_NAME} to {TO_NAME} Content Replacement (Bulletproof Edition)[/bold cyan]",
            border_style="cyan",
        )
    )

    console.print("[yellow]Running with enhanced pattern matching and import handling[/yellow]")
    console.print("[yellow]Using improved directory exclusion logic to catch all references[/yellow]")

    # First do a dry run to analyze what would be replaced
    replacements_count, sample_replacements = replace_content(dry_run=True, verbose=True)

    if not replacements_count:
        console.print(f"\n[yellow]No occurrences of '{FROM_NAME}' found to replace.[/yellow]")
        return

    # Print summary
    total_files = len(replacements_count)
    total_replacements = sum(replacements_count.values())

    summary_table = Table(show_header=False, box=box.ROUNDED)
    summary_table.add_column("Item", style="cyan")
    summary_table.add_column("Count", style="green")
    summary_table.add_row(f"Files with '{FROM_NAME}' references", str(total_files))
    summary_table.add_row("Total replacements to make", str(total_replacements))

    console.print(Panel(summary_table, title="[bold]Replacement Summary", border_style="blue"))

    # Show sample replacements
    if sample_replacements:
        console.print(f"\n[bold cyan]Sample Replacements (showing up to {MAX_REPLACEMENTS_TO_SHOW})[/bold cyan]")
        for filepath, old_text, new_text, pattern_type in sample_replacements:
            console.print(f"\n[bold blue]{filepath}[/bold blue] [magenta]({pattern_type})[/magenta]")
            console.print(f"  [red]- {escape(old_text)}[/red]")
            console.print(f"  [green]+ {escape(new_text)}[/green]")

    # Sort files by replacement count for reporting
    files_by_count = sorted(replacements_count.items(), key=lambda x: x[1], reverse=True)

    # Show top files with most replacements
    console.print("\n[bold cyan]Top Files Requiring Changes[/bold cyan]")
    files_table = Table(box=box.SIMPLE)
    files_table.add_column("File", style="blue")
    files_table.add_column("Replacements", style="green", justify="right")

    for filepath, count in files_by_count[:20]:  # Show top 20 files
        files_table.add_row(filepath, str(count))

    console.print(files_table)

    # Ask for confirmation before making changes
    confirm_message = (
        f"\nProceed with replacing {total_replacements} occurrences of '{FROM_NAME}' "
        f"with '{TO_NAME}' across {total_files} files?"
    )
    if Confirm.ask(confirm_message):
        # Perform the actual replacements
        actual_replacements, _ = replace_content(dry_run=False)
        success_message = (
            f"\n[bold green]Successfully replaced {sum(actual_replacements.values())} "
            f"occurrences in {len(actual_replacements)} files![/bold green]"
        )
        console.print(success_message)
    else:
        console.print("\n[yellow]Operation cancelled. No changes were made.[/yellow]")


if __name__ == "__main__":
    main()

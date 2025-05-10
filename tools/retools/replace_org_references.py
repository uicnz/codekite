"""Replace all occurrences of organization name references in file contents."""

import os
import re
from collections import defaultdict
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
# Terms to search for
SEARCH_TERMS = [
    "langflow-ai",
    "langflow_ai",  # Underscore variant
    "LangflowAI",   # CamelCase variant
]

# Terms to replace with (matching case)
REPLACE_TERMS = [
    "shaneholloman",
    "shaneholloman",  # Underscore variant
    "ShaneHolloman",  # CamelCase variant
]

ORG_NAME = "langflow-ai"  # Original name (for display purposes)
NEW_ORG_NAME = "shaneholloman"  # New name (for display purposes)

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
    "rename_files.py",
    "find_org_references.py",
    "replace_org_references.py"
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
MAX_REPLACEMENTS_TO_SHOW = 20  # Maximum number of replacements to show in sample output

console = Console()
# Write log files to the tools directory
TOOLS_DIR = Path(__file__).parent.absolute()
LOG_FILE = TOOLS_DIR / f"org_replacements_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"


def create_search_patterns() -> list[tuple[Pattern, str]]:
    """Create patterns and their replacements, with case preservation."""
    patterns = []

    # Create search/replacement pairs from the constants
    for i, search_term in enumerate(SEARCH_TERMS):
        replace_term = REPLACE_TERMS[i] if i < len(REPLACE_TERMS) else REPLACE_TERMS[0]
        patterns.append((re.compile(re.escape(search_term)), replace_term))

    return patterns


def categorize_match(line: str, _match: str) -> str:
    """Categorize the type of organization reference."""
    line_lower = line.lower()

    # Categorize based on context
    if "github.com" in line_lower:
        return "GitHub URL"
    if "pypi" in line_lower or "pip install" in line_lower:
        return "Package Reference"
    if "import" in line_lower or "from " in line_lower:
        return "Import Statement"
    if "http" in line_lower or "www" in line_lower:
        return "URL/Link"
    if "@" in line_lower and ("email" in line_lower or "mail" in line_lower):
        return "Email Reference"
    if "author" in line_lower or "maintainer" in line_lower:
        return "Author/Maintainer"
    if ".md" in line_lower or "documentation" in line_lower:
        return "Documentation"
    return "Other Reference"


def replace_org_references(
    root_dir: str = ".",
    *,
    dry_run: bool = True
) -> tuple[dict[str, int], list[tuple[str, str, str, str]]]:
    """Replace occurrences of organization references in file contents.

    Returns:
    - Dictionary of file paths and the number of replacements made
    - List of sample replacements with before/after context
    """
    patterns = create_search_patterns()
    replacements_count = {}
    sample_replacements = []

    # Open a log file for detailed output
    with Path(LOG_FILE).open("w") as log:
        log.write(f"Organization Reference Replacement: {ORG_NAME} -> {NEW_ORG_NAME}\n")
        # Format the timestamp in a more manageable way
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"{'DRY RUN - ' if dry_run else ''}Started at: {timestamp}\n")
        log.write("=" * 80 + "\n\n")

        # Create the progress message with operation type
        operation_type = "Analyzing" if dry_run else "Replacing"
        progress_msg = f"[bold blue]{operation_type} {ORG_NAME} references in file contents..."

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

                        # Keep track of all matches for this file (for logging)
                        file_matches = []

                        for pattern, replacement in patterns:
                            # Find all matches to track them for logging
                            matches = pattern.findall(new_content)
                            if matches:
                                for match in matches:
                                    # For each match, get some surrounding context
                                    match_pos = new_content.find(match)
                                    if match_pos >= 0:
                                        # Find line boundaries for context
                                        start = max(0, new_content.rfind("\n", 0, match_pos) + 1)
                                        end = new_content.find("\n", match_pos, min(len(new_content), match_pos + 200))
                                        if end < 0:
                                            end = min(len(new_content), match_pos + 200)

                                        # Extract before context
                                        before_context = new_content[start:match_pos + len(match)]
                                        if len(before_context) > MAX_LINE_LENGTH:
                                            before_context = "..." + before_context[-MAX_PREVIEW_LENGTH:]

                                        # Create the after context with replacement
                                        after_context = (new_content[start:match_pos] +
                                                        replacement +
                                                        new_content[match_pos + len(match):end])
                                        if len(after_context) > MAX_LINE_LENGTH:
                                            after_context = "..." + after_context[-MAX_PREVIEW_LENGTH:]

                                        category = categorize_match(before_context, match)
                                        # Add to file matches with all context data
                                        file_matches.append((
                                            match, replacement, before_context, after_context, category
                                        ))

                                        file_replacements += 1

                                # Perform the actual replacement on the content
                                new_content = pattern.sub(replacement, new_content)

                        # Only process further if changes were made
                        if file_replacements > 0:
                            replacements_count[file_path_str] = file_replacements

                            # Log details of this file's replacements
                            log.write(f"File: {file_path_str}\n")
                            log.write(f"Total replacements: {file_replacements}\n")

                            # Log each replacement with context
                            for i, (old, new, before, after, category) in enumerate(file_matches, 1):
                                log.write(f"  {i}. {category}: '{old}' -> '{new}'\n")
                                log.write(f"     Before: {before}\n")
                                log.write(f"     After:  {after}\n")

                                # Add to sample replacements for display (limit to avoid overwhelming output)
                                if len(sample_replacements) < MAX_REPLACEMENTS_TO_SHOW:
                                    sample_replacements.append((file_path_str, old, new, before, after, category))

                            log.write("-" * 60 + "\n\n")

                            # Write changes if not in dry run mode
                            if not dry_run:
                                with filepath.open("w", encoding="utf-8", errors="ignore") as f:
                                    f.write(new_content)
                                log.write(f"Changes applied to {file_path_str}\n\n")

                    except (FileNotFoundError, PermissionError, OSError) as e:
                        # Handle common file system errors specifically
                        console.print(f"[red]File system error processing {filepath}: {e!s}[/red]")
                        log.write(f"ERROR: File system error processing {filepath}: {e!s}\n")
                    except Exception as e:  # noqa: BLE001 - Catch-all needed as a critical fallback
                        # Fallback for unexpected errors to prevent script from crashing during batch operations
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
            "[bold cyan]" + f"{ORG_NAME} to {NEW_ORG_NAME} GitHub Organization Reference Replacement" +
            " (Bulletproof Edition)[/bold cyan]",
            border_style="cyan",
        )
    )

    console.print("[yellow]Using improved directory exclusion logic to catch all references[/yellow]")

    # First do a dry run to analyze what would be replaced
    replacements_count, sample_replacements = replace_org_references(dry_run=True)

    if not replacements_count:
        console.print(f"\n[yellow]No occurrences of '{ORG_NAME}' found to replace.[/yellow]")
        return

    # Print summary
    total_files = len(replacements_count)
    total_replacements = sum(replacements_count.values())

    summary_table = Table(show_header=False, box=box.ROUNDED)
    summary_table.add_column("Item", style="cyan")
    summary_table.add_column("Count", style="green")
    summary_table.add_row(f"Files with '{ORG_NAME}' references", str(total_files))
    summary_table.add_row("Total replacements to make", str(total_replacements))

    console.print(Panel(summary_table, title="[bold]Replacement Summary", border_style="blue"))

    # Group by category for reporting
    categories = defaultdict(int)
    for _, _, _, _, _, category in sample_replacements:
        categories[category] += 1

    # Print category breakdown
    if categories:
        cat_table = Table(title="Replacements by Category", box=box.SIMPLE)
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Count in Sample", style="green", justify="right")

        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            cat_table.add_row(category, str(count))

        console.print(cat_table)

    # Show sample replacements
    if sample_replacements:
        console.print(f"\n[bold cyan]Sample Replacements (showing up to {MAX_REPLACEMENTS_TO_SHOW})[/bold cyan]")
        for filepath, old, new, before, after, category in sample_replacements:
            console.print(f"\n[bold blue]{escape(filepath)}[/bold blue] [magenta]({category})[/magenta]")
            console.print(f"  Replace: [yellow]{escape(old)}[/yellow] → [green]{escape(new)}[/green]")
            console.print(f"  Before: [dim]{escape(before)}[/dim]")
            console.print(f"  After:  {escape(after)}")

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

    # Notify about log file
    console.print(f"\n[bold green]Detailed results have been logged to: [/bold green][yellow]{LOG_FILE}[/yellow]")

    # Ask for confirmation before making changes
    confirm_message = (
        f"\nProceed with replacing {total_replacements} occurrences of '{ORG_NAME}' "
        f"with '{NEW_ORG_NAME}' across {total_files} files?"
    )
    if Confirm.ask(confirm_message):
        # Perform the actual replacements
        actual_replacements, _ = replace_org_references(dry_run=False)
        success_message = (
            f"\n[bold green]Successfully replaced {sum(actual_replacements.values())} "
            f"occurrences in {len(actual_replacements)} files![/bold green]"
        )
        console.print(success_message)
    else:
        console.print("\n[yellow]Operation cancelled. No changes were made.[/yellow]")


if __name__ == "__main__":
    main()

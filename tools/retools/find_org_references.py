"""Find all occurrences of organization name references in file contents."""

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
from rich.table import Table
from rich.tree import Tree

# Configuration constants
# Terms to search for
SEARCH_TERMS = [
    "langflow-ai",
    "langflow_ai",  # Underscore variant
    "LangflowAI",   # CamelCase variant
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
MAX_RESULTS_PER_FILE = 10  # Show more results per file for org references
MAX_SAMPLE_FILES = 20      # Show more sample files
CONTEXT_LINES = 1          # Number of lines of context before/after matches

console = Console()
# Write log files to the tools directory
TOOLS_DIR = Path(__file__).parent.absolute()
LOG_FILE = TOOLS_DIR / f"org_references_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"


def create_search_pattern(terms: list[str]) -> Pattern:
    """Create a case-sensitive regex pattern from the list of terms."""
    pattern_str = "|".join(re.escape(term) for term in terms)
    return re.compile(pattern_str)


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


def find_org_references(
    root_dir: str = ".",
    max_results_per_file: int = MAX_RESULTS_PER_FILE
) -> tuple[dict[str, list[tuple[int, str, str]]], int, set[str]]:
    """Find occurrences of org references in file contents.

    Returns:
    - Dictionary of file paths to list of tuples (line_num, line_content, category)
    - Total count of occurrences
    - Set of unique repository/project references found
    """
    results = defaultdict(list)
    count = 0
    unique_repos = set()
    pattern = create_search_pattern(SEARCH_TERMS)

    # Open a log file for detailed output
    with Path(LOG_FILE).open("w") as log:
        log.write(f"Organization Reference Search: {ORG_NAME} -> {NEW_ORG_NAME}\n")
        log.write(f"Search started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write("=" * 80 + "\n\n")

        with Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]Scanning for {ORG_NAME} references in file contents..."),
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

                        # Read the file content with line numbers preserved
                        with filepath.open(errors="ignore") as f:
                            try:
                                lines = f.readlines()
                                file_matches = 0

                                for line_num, line in enumerate(lines, 1):
                                    match = pattern.search(line)
                                    if match:
                                        # Extract the actual matched text
                                        matched_text = match.group(0)

                                        # Categorize the match
                                        category = categorize_match(line, matched_text)

                                        # Only store up to max_results_per_file per file
                                        if file_matches < max_results_per_file:
                                            clean_line = line.strip()
                                            if len(clean_line) > MAX_LINE_LENGTH:
                                                clean_line = clean_line[:MAX_PREVIEW_LENGTH] + "..."

                                            # Get context lines
                                            context_lines = []
                                            for ctx_line_num in range(
                                                max(0, line_num - CONTEXT_LINES - 1),
                                                min(len(lines), line_num + CONTEXT_LINES)
                                            ):
                                                if ctx_line_num != line_num - 1:  # Skip the matched line itself
                                                    ctx_line = lines[ctx_line_num].strip()
                                                    if len(ctx_line) > MAX_LINE_LENGTH:
                                                        ctx_line = ctx_line[:MAX_PREVIEW_LENGTH] + "..."
                                                    context_lines.append((ctx_line_num + 1, ctx_line))

                                            # Add to results
                                            results[file_path_str].append(
                                                (line_num, clean_line, category, matched_text, context_lines)
                                            )

                                            # Log to file
                                            log.write(f"File: {file_path_str}\n")
                                            log.write(f"Line {line_num}: {clean_line}\n")
                                            log.write(f"Category: {category}\n")
                                            log.write(f"Matched: {matched_text}\n")
                                            for ctx_num, ctx_line in context_lines:
                                                log.write(f"Context Line {ctx_num}: {ctx_line}\n")
                                            log.write("-" * 60 + "\n\n")

                                            # Extract GitHub repos for unique list
                                            if "github.com" in line.lower():
                                                # Try to extract the full GitHub URL/path
                                                github_pattern = r"github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+"
                                                url_match = re.search(github_pattern, line)
                                                if url_match:
                                                    unique_repos.add(url_match.group(0))
                                                else:
                                                    # Just the org name with repo if we can find it
                                                    org_repo_match = re.search(
                                                        f"{re.escape(matched_text)}/[a-zA-Z0-9_-]+", line
                                                    )
                                                    if org_repo_match:
                                                        unique_repos.add(org_repo_match.group(0))

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
        log.write(f"Unique repositories referenced: {len(unique_repos)}\n")
        for repo in sorted(unique_repos):
            log.write(f"  - {repo}\n")
        log.write("=" * 80 + "\n")
        log.write(f"Search completed at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n")

    return results, count, unique_repos


def main():
    """Run the main program."""
    console.print(
        Panel.fit(
            "[bold cyan]" + f"{ORG_NAME} to {NEW_ORG_NAME} GitHub Organization Refactoring Analysis" +
            " (Bulletproof Edition)[/bold cyan]",
            border_style="cyan",
        )
    )

    console.print("[yellow]Using improved directory exclusion logic to catch all references[/yellow]")

    # Find occurrences
    results, total_count, unique_repos = find_org_references()

    # Print summary
    summary_table = Table(show_header=False, box=box.ROUNDED)
    summary_table.add_column("Item", style="cyan")
    summary_table.add_column("Count", style="green")
    summary_table.add_row(f"Total '{ORG_NAME}' references", str(total_count))
    summary_table.add_row("Files containing references", str(len(results)))
    summary_table.add_row("Unique repositories referenced", str(len(unique_repos)))

    console.print(Panel(summary_table, title="[bold]Summary", border_style="blue"))

    # Group by category
    categories = defaultdict(int)
    for matches in results.values():
        for _, _, category, _, _ in matches:
            categories[category] += 1

    # Print category breakdown
    cat_table = Table(title="References by Category", box=box.SIMPLE)
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Count", style="green", justify="right")
    cat_table.add_column("Percentage", style="yellow", justify="right")

    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_count) * 100
        cat_table.add_row(category, str(count), f"{percentage:.1f}%")

    console.print(cat_table)

    # Show GitHub repositories found
    if unique_repos:
        console.print("\n[bold cyan]GitHub Repositories Referenced[/bold cyan]")
        repo_table = Table(box=box.SIMPLE)
        repo_table.add_column("Repository", style="green")

        for repo in sorted(unique_repos):
            repo_table.add_row(repo)

        console.print(repo_table)

    # Show file tree with occurrence counts
    console.print(f"\n[bold cyan]Files with '{ORG_NAME}' references[/bold cyan]")
    grouped_by_dir = defaultdict(list)

    for filepath, matches in results.items():
        path_obj = Path(filepath)
        dirname = str(path_obj.parent)
        filename = path_obj.name
        grouped_by_dir[dirname].append((filename, len(matches)))

    file_tree = Tree("📁 [bold]Project Root[/bold]")

    for dirname, files in sorted(grouped_by_dir.items()):
        branch = file_tree if not dirname or dirname == "." else file_tree.add(f"[blue]{dirname}/[/blue]")

        for filename, count in sorted(files, key=lambda x: x[1], reverse=True):
            branch.add(f"[green]{filename}[/green] ([yellow]{count}[/yellow])")

    console.print(file_tree)

    # Print sample occurrences
    console.print(f"\n[bold cyan]Sample References[/bold cyan] (max {MAX_RESULTS_PER_FILE} per file)")
    for filepath, matches in sorted(results.items(), key=lambda x: len(x[1]), reverse=True)[:MAX_SAMPLE_FILES]:
        console.print(f"\n[bold blue]{filepath}[/bold blue]")
        for line_num, line, category, _matched, context_lines in matches:
            console.print(f"  Line {line_num} [magenta]({category})[/magenta]: [yellow]{escape(line)}[/yellow]")
            for ctx_num, ctx_line in context_lines:
                console.print(f"    Context Line {ctx_num}: [dim]{escape(ctx_line)}[/dim]")

    # Notify about log file
    console.print(f"\n[bold green]Detailed results have been logged to: [/bold green][yellow]{LOG_FILE}[/yellow]")


if __name__ == "__main__":
    main()

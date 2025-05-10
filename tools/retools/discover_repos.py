"""discover_repos.py - Automatically discover and clone repositories for refactoring."""

import argparse
import logging
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# ------ CONSTANTS ------
# Directories and Paths
DEFAULT_REPOS_DIR = "repos"
DEFAULT_LOG_PATTERN = "tools/org_replacements_*.log"

# Repositories to exclude from cloning (the main repo being refactored)
DEFAULT_EXCLUDE_REPOS = ["warpflow"]  # Don't clone the main repo we're refactoring

# Regex Patterns
ORG_REPLACEMENT_PATTERN = r"Organization Reference Replacement: ([a-zA-Z0-9_-]+) -> ([a-zA-Z0-9_-]+)"
STRING_REPLACEMENT_PATTERN = r"'([a-zA-Z0-9_-]+)' -> '([a-zA-Z0-9_-]+)'"
GITHUB_REPO_PATTERN = r"github\.com/{source_org}/([a-zA-Z0-9_-]+)"
JSDELIVR_PATTERN = r"cdn\.jsdelivr\.net/gh/{source_org}/([a-zA-Z0-9_-]+)[@/]"
RAW_GITHUB_PATTERN = r"raw\.githubusercontent\.com/{source_org}/([a-zA-Z0-9_-]+)/"
EXAMPLES_PATTERN = r"{source_org}/([a-zA-Z0-9_-]+)_examples"  # For langflow_examples
EMBEDDED_PATTERN = r"{source_org}/([a-zA-Z0-9_-]+-embedded-[a-zA-Z0-9_-]+)"  # For embedded chat
GITHUB_REFERENCE_PATTERNS = [
    GITHUB_REPO_PATTERN,  # Standard GitHub URLs
    JSDELIVR_PATTERN,     # CDN references
    RAW_GITHUB_PATTERN,   # Raw content references
    EXAMPLES_PATTERN,     # Example repositories (like langflow_examples)
    EMBEDDED_PATTERN,     # Embedded component repositories
]
FILE_SECTION_START_PATTERN = r"File: (.*?)\n"
BEFORE_AFTER_PATTERN = r"Before: (.*?)\nAfter: (.*?)$"

# Constants for validation
MIN_NAME_LENGTH = 3  # Minimum length for valid namespace names

# Rich Console setup
console = Console()
TOOLS_DIR = Path(__file__).parent.absolute()

# Log Messages
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
MSG_ORG_DISCOVERED = "Discovered organizations: {source} → {target}"
MSG_TRANSFORM_DISCOVERED = "Discovered transformations: {transforms}"
MSG_REPOS_DISCOVERED = "Discovered {count} repositories: {repos}"
MSG_PROCESSING_REPO = "Processing repository: {source} → {target}"
MSG_CLONE_SUCCESS = "Successfully cloned {repo} to {path}"
MSG_CLONE_FAIL = "Failed to clone {repo}"
MSG_REPO_EXISTS = "Repository already exists at {path}"
MSG_REPO_EXISTS_GITHUB = "Repository {repo} already exists in GitHub"
MSG_REPO_NOT_EXISTS = "Repository {repo} doesn't exist, will clone from {source}"
MSG_ERROR_ORG_DETECTION = "Could not determine source and target organizations"
MSG_LOG_NOT_FOUND = "Log file not found: {path}"
MSG_CHECK_GH_CLI = "Checking if GitHub CLI is installed and authenticated..."
MSG_GH_CLI_NOT_INSTALLED = "GitHub CLI not installed. Please install it and authenticate with 'gh auth login'"

# GitHub CLI Commands
GH_CMD_CHECK = ["gh", "--version"]
GH_CMD_VIEW_REPO = ["gh", "repo", "view", "{repo}", "--json", "name", "-q", ".name"]
GH_CMD_CLONE_REPO = ["gh", "repo", "clone", "{repo}", "{target_dir}"]


def discover_organizations(log_content: str) -> tuple[str | None, str | None]:
    """Extract source and target organization names from the log file."""
    # Look for explicit organization replacement pattern
    org_pattern = re.compile(ORG_REPLACEMENT_PATTERN)
    match = org_pattern.search(log_content)
    if match:
        return match.group(1), match.group(2)  # source_org, target_org

    # Fallback: look for string replacement patterns in the log
    replacements = re.findall(STRING_REPLACEMENT_PATTERN, log_content)
    if replacements:
        # Analyze the most common replacement pattern
        return replacements[0][0], replacements[0][1]

    return None, None


def discover_namespace_transformation(log_content: str) -> dict[str, str]:
    """Determine namespace transformation rules from log content."""
    transformations = {}

    # Extract sections with Before/After patterns directly
    # This pattern looks for "Before:" and "After:" lines in the log file
    before_after_matches = re.findall(BEFORE_AFTER_PATTERN, log_content, re.MULTILINE)
    for before, after in before_after_matches:
        # We're especially interested in repository name transformations
        # For example: warpflow-bundles → warpflow-bundles
        before_parts = before.strip().split("/")
        after_parts = after.strip().split("/")

        if len(before_parts) > 0 and len(after_parts) > 0:
            # Compare the last parts which are typically repo names
            # Get the repo name from path parts (using last non-empty part or fallback to second-last)
            before_repo = (
                before_parts[-1] if before_parts[-1]
                else (before_parts[-2] if len(before_parts) > 1 else "")
            )
            after_repo = after_parts[-1] if after_parts[-1] else (after_parts[-2] if len(after_parts) > 1 else "")

            if before_repo and after_repo and before_repo != after_repo:
                # Look for consistent prefix/suffix transformations
                before_prefix = before_repo.split("-")[0] if "-" in before_repo else before_repo
                after_prefix = after_repo.split("-")[0] if "-" in after_repo else after_repo

                if before_prefix != after_prefix:
                    transformations[before_prefix] = after_prefix

    # If no transformations found, try a more general approach
    if not transformations:
        # Look for all pairs of words that might be replaced
        all_replacements = re.findall(r"'([a-zA-Z0-9_-]+)' -> '([a-zA-Z0-9_-]+)'", log_content)
        # Use dictionary comprehension instead of loop
        transformations = {
            old: new for old, new in all_replacements
            if old != new and len(old) > MIN_NAME_LENGTH  # Avoid trivial replacements
        }

    return transformations


def discover_repositories(log_content: str, source_org: str) -> set[str]:
    """Extract all repositories referenced in the log file."""
    repos = set()
    escaped_org = re.escape(source_org)

    # Search for each pattern type and collect repositories
    for pattern_template in GITHUB_REFERENCE_PATTERNS:
        pattern = pattern_template.format(source_org=escaped_org)
        repo_pattern = re.compile(pattern)

        for match in repo_pattern.finditer(log_content):
            repo_name = match.group(1)
            # Exclude non-repo paths and ensure it's a valid repo name
            if "/" not in repo_name and "." not in repo_name:
                # Special case for examples repositories (like langflow_examples)
                if pattern_template == EXAMPLES_PATTERN:
                    repos.add(f"{repo_name}_examples")
                else:
                    repos.add(repo_name)

    # Also specifically look for embedded-chat and examples with explicit patterns
    embedded_chat_pattern = re.compile(r"warpflow-embedded-chat")
    examples_pattern = re.compile(r"langflow_examples")

    if embedded_chat_pattern.search(log_content):
        repos.add("warpflow-embedded-chat")

    if examples_pattern.search(log_content):
        # Check API references which might indicate external repositories
        api_examples_pattern = re.compile(r"warpflow_examples/main/examples|langflow_examples/main/examples")
        if api_examples_pattern.search(log_content):
            logging.info("Found examples repository referenced in API paths")
            repos.add("langflow_examples")

    # Log what was found
    found_repos = ", ".join(sorted(repos))
    logging.info("Found repositories using patterns: %s", found_repos)

    return repos


def transform_repo_name(repo_name: str, transformations: dict[str, str]) -> str:
    """Apply namespace transformations to repository names."""
    new_name = repo_name
    for old, new in transformations.items():
        new_name = new_name.replace(old, new)
    return new_name


def check_gh_cli_installed() -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    logging.info(MSG_CHECK_GH_CLI)
    try:
        subprocess.run(GH_CMD_CHECK, capture_output=True, check=True)  # noqa: S603
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.exception(MSG_GH_CLI_NOT_INSTALLED)
        return False
    else:
        return True


def clone_repository(source_org: str, target_org: str, repo_name: str,
                    new_repo_name: str, repos_dir: str) -> bool:
    """Clone a repository using GitHub CLI."""
    # Special case for langflow_examples which may be named differently
    if repo_name == "langflow_examples":
        # Try alternative repository names
        alternatives = [
            f"{source_org}/warpflow-examples",  # Try with hyphen instead of underscore
        ]

        for alt_repo in alternatives:
            logging.info("Trying alternative repository: %s", alt_repo)
            source_repo = alt_repo
            target_dir = Path(repos_dir) / new_repo_name

            # Check if repository already exists locally
            if target_dir.exists():
                logging.info(MSG_REPO_EXISTS.format(path=target_dir))
                return True

            # Try to clone directly
            clone_cmd = [
                "gh", "repo", "clone", source_repo, str(target_dir)
            ]

            try:
                subprocess.run(clone_cmd, check=True, capture_output=True)  # noqa: S603
            except subprocess.CalledProcessError:
                logging.info("Failed to clone alternative repository: %s", alt_repo)
                continue
            else:
                return True

        # If we're here, we couldn't find the examples repository
        logging.warning("Could not find examples repository with any known name variant")
        return False

    # Standard repository cloning logic
    source_repo = f"{source_org}/{repo_name}"
    target_dir = Path(repos_dir) / new_repo_name

    # Check if repository already exists locally
    if target_dir.exists():
        logging.info(MSG_REPO_EXISTS.format(path=target_dir))
        return True

    # Check if repository exists in target organization
    target_repo = f"{target_org}/{new_repo_name}"
    # Use list comprehension instead of a for loop
    check_cmd = [
        cmd.format(repo=target_repo) if "{repo}" in cmd else cmd
        for cmd in GH_CMD_VIEW_REPO
    ]

    try:
        subprocess.run(check_cmd, capture_output=True, check=True)  # noqa: S603
        logging.info(MSG_REPO_EXISTS_GITHUB.format(repo=target_repo))
        # Clone the existing repository from target organization
        clone_cmd = []
        for cmd in GH_CMD_CLONE_REPO:
            if "{repo}" in cmd:
                clone_cmd.append(cmd.format(repo=target_repo))
            elif "{target_dir}" in cmd:
                clone_cmd.append(cmd.format(target_dir=target_dir))
            else:
                clone_cmd.append(cmd)
    except subprocess.CalledProcessError:
        logging.info(MSG_REPO_NOT_EXISTS.format(repo=target_repo, source=source_repo))
        # Clone from source organization
        clone_cmd = []
        for cmd in GH_CMD_CLONE_REPO:
            if "{repo}" in cmd:
                clone_cmd.append(cmd.format(repo=source_repo))
            elif "{target_dir}" in cmd:
                clone_cmd.append(cmd.format(target_dir=target_dir))
            else:
                clone_cmd.append(cmd)

    try:
        subprocess.run(clone_cmd, check=True)  # noqa: S603
    except subprocess.CalledProcessError:
        # Use string format instead of f-string for logging
        logging.exception(MSG_CLONE_FAIL.format(repo=repo_name))
        return False
    else:
        return True


def find_latest_log(pattern: str = DEFAULT_LOG_PATTERN) -> str | None:
    """Find the most recent org_replacements log file."""
    # Use Path.glob instead of glob.glob
    log_files = list(Path().glob(pattern))
    if not log_files:
        return None

    # Sort by modification time, newest first using Path.stat()
    return str(sorted(log_files, key=lambda p: p.stat().st_mtime, reverse=True)[0])


def setup_logging() -> None:
    """Configure logging for the script."""
    log_file = TOOLS_DIR / f"discover_repos_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file)
        ]
    )
    return log_file


def main() -> int:
    """Main script execution."""
    # Display welcome header
    console.print(
        Panel.fit(
            "[bold cyan]Repository Discovery and Cloning Tool[/bold cyan]",
            border_style="cyan",
        )
    )

    log_file = setup_logging()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Discover and clone repositories for refactoring")
    parser.add_argument("-l", "--log", help="Path to replacements log file")
    parser.add_argument("-d", "--dir", default=DEFAULT_REPOS_DIR,
                        help=f"Directory to clone repositories into (default: {DEFAULT_REPOS_DIR})")
    parser.add_argument("-e", "--exclude", nargs="+", default=[],
                        help="Additional repositories to exclude from cloning")
    args = parser.parse_args()

    console.print(f"[bold blue]Log file:[/bold blue] {log_file}")

    # Find log file or use the provided one
    log_path = args.log or find_latest_log()
    if not log_path or not Path(log_path).exists():
        logging.error(MSG_LOG_NOT_FOUND.format(path=log_path))
        return 1

    repos_dir = args.dir

    # Verify GitHub CLI is available
    if not check_gh_cli_installed():
        return 1

    # Read log content using Path
    log_content = Path(log_path).read_text()

    # Discover organizations
    source_org, target_org = discover_organizations(log_content)
    if not source_org or not target_org:
        logging.error(MSG_ERROR_ORG_DETECTION)
        return 1

    # Display organization discovery results
    console.print("\n[bold green]Organization Discovery[/bold green]")
    console.print(f"Source organization: [cyan]{source_org}[/cyan]")
    console.print(f"Target organization: [cyan]{target_org}[/cyan]")
    logging.info(MSG_ORG_DISCOVERED.format(source=source_org, target=target_org))

    # Discover namespace transformations
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Discovering namespace transformations..."),
        transient=True,
    ) as progress:
        task = progress.add_task("Analyzing", total=None)
        transformations = discover_namespace_transformation(log_content)
        progress.update(task, completed=True)

    # Display transformations in a table
    if transformations:
        transform_table = Table(title="Namespace Transformations", box=box.ROUNDED)
        transform_table.add_column("From", style="yellow")
        transform_table.add_column("To", style="green")

        for old, new in transformations.items():
            transform_table.add_row(old, new)

        console.print(transform_table)
    else:
        console.print("[yellow]No namespace transformations discovered[/yellow]")

    logging.info(MSG_TRANSFORM_DISCOVERED.format(transforms=transformations))

    # Discover repositories
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Discovering repositories..."),
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning", total=None)
        repositories = discover_repositories(log_content, source_org)
        progress.update(task, completed=True)

    # Display repositories in a table
    if repositories:
        repo_table = Table(title="Discovered Repositories", box=box.ROUNDED)
        repo_table.add_column("Original Name", style="yellow")
        repo_table.add_column("New Name", style="green")

        for repo in sorted(repositories):
            new_repo = transform_repo_name(repo, transformations)
            repo_table.add_row(repo, new_repo)

        console.print(repo_table)
    else:
        console.print("[yellow]No repositories discovered[/yellow]")

    repo_list = ", ".join(repositories)
    logging.info(MSG_REPOS_DISCOVERED.format(count=len(repositories), repos=repo_list))

    # Create repos directory using Path
    Path(repos_dir).mkdir(parents=True, exist_ok=True)
    console.print(f"\n[bold blue]Cloning repositories to:[/bold blue] {repos_dir}")

    # Get the list of repos to exclude (combining defaults with any user-specified ones)
    exclude_repos = DEFAULT_EXCLUDE_REPOS + args.exclude
    if exclude_repos:
        console.print(f"\n[bold yellow]Excluding repositories:[/bold yellow] {', '.join(exclude_repos)}")

    # Filter out excluded repositories
    repositories_to_clone = [repo for repo in repositories if repo not in exclude_repos]
    skipped_repos = [repo for repo in repositories if repo in exclude_repos]

    if skipped_repos:
        skipped_list = ", ".join(skipped_repos)
        console.print(f"[yellow]Skipping {len(skipped_repos)} excluded repositories: {skipped_list}[/yellow]")

    # Clone repositories with progress tracking
    results = {"success": [], "failed": [], "skipped": skipped_repos}

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Cloning repositories..."),
    ) as progress:
        task = progress.add_task("Cloning", total=len(repositories_to_clone))

        for repo in repositories_to_clone:
            new_repo = transform_repo_name(repo, transformations)
            progress.update(task, description=f"Cloning {repo} → {new_repo}")
            logging.info(MSG_PROCESSING_REPO.format(source=repo, target=new_repo))

            if clone_repository(source_org, target_org, repo, new_repo, repos_dir):
                success_path = str(Path(repos_dir) / new_repo)
                results["success"].append((repo, new_repo, success_path))
                logging.info(MSG_CLONE_SUCCESS.format(repo=repo, path=success_path))
            else:
                results["failed"].append((repo, new_repo))
                logging.error(MSG_CLONE_FAIL.format(repo=repo))

            progress.update(task, advance=1)

    # Display results summary
    summary_table = Table(title="Cloning Results", box=box.ROUNDED)
    summary_table.add_column("Result", style="cyan")
    summary_table.add_column("Count", style="green")
    summary_table.add_row("Repositories cloned successfully", str(len(results["success"])))
    summary_table.add_row("Repositories failed to clone", str(len(results["failed"])))
    summary_table.add_row("Repositories skipped (excluded)", str(len(results["skipped"])))

    console.print(summary_table)

    # Show success details
    if results["success"]:
        console.print("\n[bold green]Successfully Cloned Repositories:[/bold green]")
        for repo, new_repo, path in results["success"]:
            console.print(f"✓ [cyan]{repo}[/cyan] → [green]{new_repo}[/green] at [blue]{path}[/blue]")

    # Show failure details
    if results["failed"]:
        console.print("\n[bold red]Failed to Clone:[/bold red]")
        for repo, new_repo in results["failed"]:
            console.print(f"✗ [cyan]{repo}[/cyan] → [yellow]{new_repo}[/yellow]")

    # Show skipped repositories
    if results["skipped"]:
        console.print("\n[bold yellow]Skipped Repositories (Excluded):[/bold yellow]")
        for repo in results["skipped"]:
            new_repo = transform_repo_name(repo, transformations)
            console.print(f"→ [cyan]{repo}[/cyan] → [blue]{new_repo}[/blue]")

    console.print("\n[bold green]Cloning operation complete![/bold green]")
    console.print(f"Detailed log available at: [blue]{log_file}[/blue]")
    return 0


if __name__ == "__main__":
    sys.exit(main())

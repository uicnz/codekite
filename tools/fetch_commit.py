#!/usr/bin/env python3
"""
Fetch files from a specific GitHub commit

This script uses the GitHub CLI to download all files that were changed in a specific
commit, preserving the original directory structure.

Usage:
    python fetch_commit.py owner/repo commit_hash [--output-dir DIR]

Examples:
    # Use the default 'tmp-commits' directory in the project root
    python fetch_commit.py shaneholloman/kit ddafb6b3042284baba79fac0a370d91ede43f52d

    # Specify a custom output directory
    python fetch_commit.py shaneholloman/kit ddafb6b3042284baba79fac0a370d91ede43f52d --output-dir custom-dir
"""

import os
import sys
import subprocess
import argparse
import datetime
from typing import List


def check_gh_cli() -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        subprocess.run(["gh", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_commit_files(repo: str, commit_hash: str) -> List[str]:
    """Get list of files changed in a commit."""
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/commits/{commit_hash}", "--jq", ".files[].filename"],
            check=True,
            capture_output=True,
            text=True
        )

        # Split the output by newlines and remove empty strings
        files = [file.strip() for file in result.stdout.strip().split("\n") if file.strip()]
        return files
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Error getting files: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)


def download_file(repo: str, file_path: str, commit_hash: str, output_dir: str) -> bool:
    """Download a file from a specific commit."""
    try:
        # Create directory structure if it doesn't exist
        full_path = os.path.join(output_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Get file content via GitHub API
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{file_path}?ref={commit_hash}", "--jq", ".content"],
            check=True,
            capture_output=True,
            text=True
        )

        # If content is empty, try a different approach (it might be a binary file or too large)
        if not result.stdout.strip():
            # Try to download the raw file directly
            raw_url = f"https://raw.githubusercontent.com/{repo}/{commit_hash}/{file_path}"
            print(f"[INFO] Downloading from {raw_url}")

            subprocess.run(
                ["curl", "-s", "-L", "-o", full_path, raw_url],
                check=True
            )
        else:
            # Decode base64 content
            with open(full_path, "wb") as f:
                # Use the built-in base64 module to decode
                import base64
                content = result.stdout.strip()
                # GitHub API sometimes adds newlines, so remove them
                content = content.replace("\n", "")
                try:
                    f.write(base64.b64decode(content))
                except Exception as e:
                    print(f"[WARN] Base64 decode failed: {e}")
                    print("[INFO] Trying to download directly...")
                    # If base64 decoding fails, try direct download
                    raw_url = f"https://raw.githubusercontent.com/{repo}/{commit_hash}/{file_path}"
                    subprocess.run(
                        ["curl", "-s", "-L", "-o", full_path, raw_url],
                        check=True
                    )

        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Error downloading {file_path}: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch files from a specific GitHub commit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("repo", help="Repository name in format 'owner/repo'")
    parser.add_argument("commit", help="Commit hash")
    parser.add_argument("--output-dir", "-o",
                        help="Output directory (if not specified, a temporary directory will be created)")

    args = parser.parse_args()

    # Check if GitHub CLI is installed
    if not check_gh_cli():
        print("[FAIL] GitHub CLI (gh) is not installed or not authenticated.")
        print("Please install GitHub CLI and run 'gh auth login'")
        sys.exit(1)

    # Create output directory (use project's tmp-commits directory if not specified)
    if args.output_dir:
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)
    else:
        # Create a tmp-commits directory in the project root
        base_tmp_dir = os.path.join(os.getcwd(), "tmp-commits")
        os.makedirs(base_tmp_dir, exist_ok=True)

        # Create a unique subdirectory for this commit
        commit_short = args.commit[:8]  # Use first 8 chars of commit hash
        repo_name = args.repo.split("/")[-1]  # Extract repo name from owner/repo
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        dir_name = f"{repo_name}-{commit_short}-{timestamp}"
        output_dir = os.path.join(base_tmp_dir, dir_name)
        os.makedirs(output_dir, exist_ok=True)

        print(f"[INFO] Using directory: {output_dir}")

    print(f"[INFO] Fetching files from {args.repo} commit {args.commit}")

    # Get list of files changed in the commit
    print("[INFO] Getting list of changed files...")
    files = get_commit_files(args.repo, args.commit)

    if not files:
        print(f"[FAIL] No files found in commit {args.commit}")
        sys.exit(1)

    print(f"[INFO] Found {len(files)} files to download")

    # Download each file
    success_count = 0
    downloaded_files = []
    failed_files = []

    for i, file_path in enumerate(files, 1):
        print(f"[INFO] Downloading {i}/{len(files)}: {file_path}")
        if download_file(args.repo, file_path, args.commit, output_dir):
            success_count += 1
            downloaded_files.append(file_path)
            print(f"[PASS] Downloaded {file_path}")
        else:
            failed_files.append(file_path)
            print(f"[FAIL] Failed to download {file_path}")

    print(f"[PASS] Downloaded {success_count}/{len(files)} files from commit {args.commit}")
    print(f"[INFO] Files saved to {output_dir}")

    # Save list of files to a manifest file
    manifest_path = os.path.join(output_dir, "manifest.txt")
    with open(manifest_path, "w") as f:
        f.write(f"# Files from {args.repo} commit {args.commit}\n")
        f.write(f"# Downloaded on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total: {success_count} files\n\n")
        for file_path in downloaded_files:
            f.write(f"{file_path}\n")

    print(f"[INFO] File manifest saved to {manifest_path}")


if __name__ == "__main__":
    main()

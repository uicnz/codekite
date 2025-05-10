"""Tests for the ContextAssembler component's handling of size and content limits.

The ContextAssembler formats code context for LLM prompts and needs to handle
various types of size limits to prevent exceeding token limits, including:
- Skipping files by name/pattern
- Skipping files that exceed line/byte/token count
- Truncating or summarizing content that exceeds limits
- Prioritizing files when total context size is limited
"""

from pathlib import Path
from codekite import Repository


def make_repo(tmp_path: Path) -> Path:
    """Create a test repository directory.

    Parameters
    ----------
    tmp_path : Path
        Pytest temporary directory fixture

    Returns
    -------
    Path
        Path to the created repository root
    """
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    return repo_root


def test_skip_by_filename(tmp_path: Path) -> None:
    """Test that files can be skipped based on filename patterns.

    Files like package-lock.json, node_modules, or large generated files
    should be excludable based on name patterns to avoid including
    irrelevant content in the context.
    """
    repo_root = make_repo(tmp_path)
    (repo_root / "package-lock.json").write_text("{}\n")
    (repo_root / "important.py").write_text("print('important')\n")

    repo = Repository(str(repo_root))
    assembler = repo.get_context_assembler()

    # Add both files but skip the lock file
    assembler.add_file(
        "package-lock.json",
        skip_if_name_in=["package-lock.json", "yarn.lock", "node_modules"],
    )
    assembler.add_file("important.py")

    ctx = assembler.format_context()
    # Lock file should be skipped but important file included
    assert "package-lock.json" not in ctx
    assert "important.py" in ctx


def test_skip_by_max_lines(tmp_path: Path) -> None:
    """Test that files exceeding a maximum line count are skipped.

    Large files that exceed a specific line count threshold should be
    excluded from the context to maintain reasonable context sizes.
    """
    repo_root = make_repo(tmp_path)
    big_file = repo_root / "big.py"
    big_file.write_text("\n".join([f"print('line_{i}')" for i in range(500)]))

    repo = Repository(str(repo_root))
    assembler = repo.get_context_assembler()

    assembler.add_file("big.py", max_lines=100)
    ctx = assembler.format_context()
    assert "big.py" not in ctx

    # Verify with exactly at the limit
    medium_file = repo_root / "medium.py"
    medium_file.write_text("\n".join([f"print('line_{i}')" for i in range(100)]))

    assembler = repo.get_context_assembler()
    assembler.add_file("medium.py", max_lines=100)
    ctx = assembler.format_context()
    assert "medium.py" in ctx


def test_include_small_file(tmp_path: Path) -> None:
    """Test that small files under the line limit are included.

    Files below the specified line count threshold should be included
    in the context.
    """
    repo_root = make_repo(tmp_path)
    small = repo_root / "small.py"
    small.write_text("print('hi')\n")

    repo = Repository(str(repo_root))
    assembler = repo.get_context_assembler()
    assembler.add_file("small.py", max_lines=100)

    ctx = assembler.format_context()
    assert "small.py" in ctx
    assert "print('hi')" in ctx


def test_skip_by_file_size(tmp_path: Path) -> None:
    """Test that files exceeding a maximum byte size are skipped.

    Files larger than a specific byte size should be excluded from
    the context, which is important for binary files or files with
    very long lines.
    """
    repo_root = make_repo(tmp_path)

    # Create a file with one very long line
    long_line_file = repo_root / "long_line.py"
    long_line_file.write_text("x = '" + "a" * 10000 + "'\n")

    repo = Repository(str(repo_root))
    assembler = repo.get_context_assembler()

    # Test with byte size limit
    assembler.add_file("long_line.py", max_bytes=5000)
    ctx = assembler.format_context()
    assert "long_line.py" not in ctx

    # Create a file under the limit
    small_file = repo_root / "small_file.py"
    small_file.write_text("x = 'small'\n")

    assembler = repo.get_context_assembler()
    assembler.add_file("small_file.py", max_bytes=5000)
    ctx = assembler.format_context()
    assert "small_file.py" in ctx


def test_multiple_files_with_limits(tmp_path: Path) -> None:
    """Test handling multiple files with mixed sizes and different limits.

    Tests the context assembler's ability to correctly apply different
    limit rules to multiple files in the same context.
    """
    repo_root = make_repo(tmp_path)

    # Create multiple files with different sizes
    files = {
        "small.py": "print('small')\n",
        "medium.py": "\n".join([f"print({i})" for i in range(50)]),
        "large.py": "\n".join([f"print({i})" for i in range(200)]),
        "package-lock.json": "{ " + '"dependencies": {}'.ljust(5000) + " }"
    }

    for name, content in files.items():
        (repo_root / name).write_text(content)

    repo = Repository(str(repo_root))
    assembler = repo.get_context_assembler()

    # Add files with different limit rules
    assembler.add_file("small.py")  # No limits
    assembler.add_file("medium.py", max_lines=100)  # Under line limit
    assembler.add_file("large.py", max_lines=100)  # Over line limit
    assembler.add_file("package-lock.json", skip_if_name_in=["package-lock.json"])

    ctx = assembler.format_context()

    # Check correct files were included/excluded
    assert "small.py" in ctx
    assert "medium.py" in ctx
    assert "large.py" not in ctx
    assert "package-lock.json" not in ctx


def test_line_limit_behavior(tmp_path: Path) -> None:
    """Test behavior with files at the line limit boundary.

    Verify that files exactly at the line limit are included,
    while files exceeding the limit are excluded.
    """
    repo_root = make_repo(tmp_path)

    # Create files with different line counts
    (repo_root / "at_limit.py").write_text("\n".join([f"print('line_{i}')" for i in range(100)]))
    (repo_root / "over_limit.py").write_text("\n".join([f"print('line_{i}')" for i in range(101)]))
    (repo_root / "under_limit.py").write_text("\n".join([f"print('line_{i}')" for i in range(99)]))

    repo = Repository(str(repo_root))
    assembler = repo.get_context_assembler()

    # Add all files with the same line limit
    assembler.add_file("at_limit.py", max_lines=100)
    assembler.add_file("over_limit.py", max_lines=100)
    assembler.add_file("under_limit.py", max_lines=100)

    ctx = assembler.format_context()

    # Check correct inclusion/exclusion
    assert "at_limit.py" in ctx
    assert "over_limit.py" not in ctx
    assert "under_limit.py" in ctx


def test_multiple_limit_types(tmp_path: Path) -> None:
    """Test applying multiple types of limits to the same file.

    Verify that when multiple limit types are specified, all limits
    are respected (the file is excluded if ANY limit is exceeded).
    """
    repo_root = make_repo(tmp_path)

    # Create test files
    (repo_root / "many_short_lines.py").write_text("\n".join(["x=1"] * 200))  # Many lines but few bytes per line
    (repo_root / "few_long_lines.py").write_text("\n".join(["x='" + "a" * 1000 + "'"] * 3))  # Few lines but many bytes

    repo = Repository(str(repo_root))
    assembler = repo.get_context_assembler()

    # Apply both limit types
    assembler.add_file("many_short_lines.py", max_lines=100, max_bytes=5000)
    assembler.add_file("few_long_lines.py", max_lines=100, max_bytes=500)

    ctx = assembler.format_context()

    # Line count excludes first file, byte count excludes second file
    assert "many_short_lines.py" not in ctx
    assert "few_long_lines.py" not in ctx

    # Add with limits that allow inclusion
    assembler = repo.get_context_assembler()
    assembler.add_file("many_short_lines.py", max_lines=300, max_bytes=5000)
    assembler.add_file("few_long_lines.py", max_lines=100, max_bytes=5000)

    ctx = assembler.format_context()

    # Both files should now be included
    assert "many_short_lines.py" in ctx
    assert "few_long_lines.py" in ctx


def test_skip_by_exact_filename(tmp_path: Path) -> None:
    """Test skipping files by exact filename.

    The current implementation of skip_if_name_in only checks against
    the exact filename, not the path or wildcard patterns.
    """
    repo_root = make_repo(tmp_path)

    # Create various files
    files = {
        "package-lock.json": "{}",
        "yarn.lock": "yarn-stuff",
        "module.js": "module.exports = {};",
        "output.js": "console.log('built')",
        "bundle.js": "// bundled code",
        "important.js": "// Keep this file",
    }

    for path, content in files.items():
        file_path = repo_root / path
        file_path.write_text(content)

    repo = Repository(str(repo_root))
    assembler = repo.get_context_assembler()

    # Add all files but skip by exact filenames
    skip_patterns = [
        "package-lock.json",
        "yarn.lock",
        "module.js",
    ]

    for file_name in files.keys():
        assembler.add_file(file_name, skip_if_name_in=skip_patterns)

    ctx = assembler.format_context()

    # Check correct inclusions/exclusions
    assert "important.js" in ctx
    assert "output.js" in ctx
    assert "bundle.js" in ctx
    assert "package-lock.json" not in ctx
    assert "yarn.lock" not in ctx
    assert "module.js" not in ctx

#!/bin/bash
#
# clean-dotfiles.sh
#
# This script removes macOS dot-underscore (._) files and other
# macOS-specific metadata files from the specified directory.
#
# Usage: ./clean-dotfiles.sh [directory]
#        If no directory is specified, the current directory is used.

set -e

# Default to current directory if no argument provided
TARGET_DIR="${1:-.}"

echo "=== macOS Metadata File Cleaner ==="
echo "Target directory: $TARGET_DIR"
echo

# Function to count files
count_files() {
  find "$TARGET_DIR" -name "._*" | wc -l | tr -d ' '
}

# Count files before cleaning
BEFORE_COUNT=$(count_files)
echo "Found $BEFORE_COUNT dot-underscore files to clean"

if [ "$BEFORE_COUNT" -gt 0 ]; then
  echo "Removing dot-underscore files..."
  find "$TARGET_DIR" -name "._*" -delete
  echo "Done!"
else
  echo "No dot-underscore files found."
fi

# Run dot_clean to merge resource forks
echo
echo "Running dot_clean to merge any resource forks with their original files..."
dot_clean "$TARGET_DIR"
echo "Done!"

# Count files after cleaning
AFTER_COUNT=$(count_files)
echo
echo "Cleanup complete! Removed $((BEFORE_COUNT - AFTER_COUNT)) dot-underscore files."

echo
echo "=== Preventing Future Dot-Underscore Files ==="
echo "To prevent macOS from creating these files in the future, you can:"
echo
echo "1. Set the COPYFILE_DISABLE environment variable before file operations:"
echo "   export COPYFILE_DISABLE=1"
echo
echo "2. For tar operations, use the --disable-copyfile option:"
echo "   tar --disable-copyfile -czf archive.tar.gz directory/"
echo
echo "3. Add this to your .bash_profile or .zshrc to make it permanent:"
echo "   # Prevent creation of ._* files on non-HFS+ volumes"
echo "   export COPYFILE_DISABLE=1"
echo
echo "4. Use this script periodically to clean up any files that do get created"
echo

exit 0

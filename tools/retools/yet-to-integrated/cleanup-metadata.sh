#!/bin/bash

# Configuration
REPOS_DIR="." # Should match the directory in sync-forks.sh

# Define colors without bold formatting
BLUE="\033[34m"    # Blue
GREEN="\033[32m"   # Green
RED="\033[31m"     # Red
YELLOW="\033[33m"  # Yellow
MAGENTA="\033[35m" # Magenta
CYAN="\033[36m"    # Cyan
RESET="\033[0m"

# Ensure the directory exists
if [ ! -d "$REPOS_DIR" ]; then
  echo -e "${RED}Error: Repository directory $REPOS_DIR does not exist.${RESET}"
  exit 1
fi

echo -e "${CYAN}=== macOS Metadata Cleanup Tool ===${RESET}"
echo -e "${YELLOW}Starting cleanup of macOS metadata files in:${RESET}"
echo -e "${MAGENTA}$REPOS_DIR${RESET}"
echo -e "${YELLOW}Time: $(date)${RESET}"
echo -e "${CYAN}Processing repositories one by one with progress indicators...${RESET}"
echo

# Initialize counters
TOTAL_DELETED=0
REPO_COUNT=0

# Process each repository directory separately for better progress tracking
for repo_dir in "$REPOS_DIR"/*; do
  if [ -d "$repo_dir" ]; then
    ((REPO_COUNT++))
    repo_name=$(basename "$repo_dir")

    echo -e "${CYAN}[$REPO_COUNT] Processing repository: ${MAGENTA}$repo_name${RESET} at $(date)"

    # Count and delete ._* files in this repository
    DOT_FILES=$(find "$repo_dir" -name "._*" -type f | wc -l)

    if [ "$DOT_FILES" -gt 0 ]; then
      echo -e "${GREEN}  ✓ Found $DOT_FILES ._* files in $repo_name${RESET}"
      echo -e "${GREEN}  ✓ Deleting ._* files from $repo_name...${RESET}"
      find "$repo_dir" -name "._*" -type f -delete
      echo -e "${GREEN}  ✓ Deleted $DOT_FILES ._* files from $repo_name at $(date)${RESET}"
      TOTAL_DELETED=$((TOTAL_DELETED + DOT_FILES))
    else
      echo -e "${BLUE}  ✗ No ._* files found in $repo_name${RESET}"
    fi

    # Count and delete .DS_Store files in this repository
    DS_FILES=$(find "$repo_dir" -name ".DS_Store" -type f | wc -l)
    if [ "$DS_FILES" -gt 0 ]; then
      echo -e "${GREEN}  ✓ Found $DS_FILES .DS_Store files in $repo_name${RESET}"
      echo -e "${GREEN}  ✓ Deleting $DS_FILES .DS_Store files from $repo_name...${RESET}"
      find "$repo_dir" -name ".DS_Store" -type f -delete
      TOTAL_DELETED=$((TOTAL_DELETED + DS_FILES))
    else
      echo -e "${BLUE}  ✗ No .DS_Store files found in $repo_name${RESET}"
    fi

    if [ "$DOT_FILES" -gt 0 ] || [ "$DS_FILES" -gt 0 ]; then
      echo -e "${GREEN}  ✓ Completed $repo_name ($REPO_COUNT repositories processed, $TOTAL_DELETED files deleted so far)${RESET}"
    else
      echo -e "${BLUE}  ✗ Completed $repo_name ($REPO_COUNT repositories processed, $TOTAL_DELETED files deleted so far)${RESET}"
    fi
    echo -e "${CYAN}------------------------------------------------------${RESET}"
  fi
done

echo
echo -e "${CYAN}=== Cleanup Summary ===${RESET}"
echo -e "${YELLOW}Cleanup complete at $(date)${RESET}"
echo -e "${YELLOW}Processed $REPO_COUNT repositories${RESET}"
if [ "$TOTAL_DELETED" -gt 0 ]; then
  echo -e "${GREEN}✓ Successfully deleted $TOTAL_DELETED macOS metadata files${RESET}"
else
  echo -e "${BLUE}✗ No macOS metadata files found to delete${RESET}"
fi
echo -e "${CYAN}=== Done! ===${RESET}"

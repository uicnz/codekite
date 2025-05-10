import os
import re
import pathlib
import shutil
import traceback
import yaml # For front matter parsing

# --- Function to parse front matter ---
def parse_front_matter(content):
    """Extracts slug or id from YAML front matter."""
    slug = None
    fm_id = None
    try:
        if content.startswith('---'):
            end_fm = content.find('---', 3)
            if end_fm != -1:
                front_matter_str = content[3:end_fm]
                # Basic check for slug or id lines before full YAML parse
                if 'slug:' in front_matter_str or 'id:' in front_matter_str:
                    try:
                        front_matter = yaml.safe_load(front_matter_str)
                        if isinstance(front_matter, dict):
                            slug = front_matter.get('slug')
                            fm_id = front_matter.get('id')
                            # Clean slug if found
                            if isinstance(slug, str):
                                slug = slug.strip('/')
                            else:
                                slug = None # Ensure slug is None if not a string
                            # Clean id if found
                            if not isinstance(fm_id, str):
                                fm_id = None # Ensure id is None if not a string

                    except yaml.YAMLError as e:
                        # print(f"    [WARN] Could not parse YAML front matter: {e}")
                        # Fallback to regex for simple cases if YAML fails
                        slug_match = re.search(r'^\s*slug:\s*["\']?([^"\']+)["\']?\s*$', front_matter_str, re.MULTILINE)
                        if slug_match:
                            slug = slug_match.group(1).strip('/')
                        id_match = re.search(r'^\s*id:\s*["\']?([^"\']+)["\']?\s*$', front_matter_str, re.MULTILINE)
                        if id_match:
                            fm_id = id_match.group(1)

    except Exception as e:
        print(f"    [ERROR] Unexpected error parsing front matter: {e}")

    return slug, fm_id


# --- Function to build slug/id map from files ---
def build_file_map(docs_dir: pathlib.Path):
    """Scans all markdown files, parses front matter, and builds a map."""
    file_map = {}
    print(f"\nScanning files in {docs_dir} for slugs/IDs...")
    count = 0
    for md_file in docs_dir.rglob('*.md'):
        count += 1
        try:
            content = md_file.read_text(encoding='utf-8')
            slug, fm_id = parse_front_matter(content)
            abs_path = md_file.resolve()

            # Prefer slug if available
            if slug:
                if slug in file_map:
                     print(f"  [WARN] Duplicate slug '{slug}' found. Overwriting mapping for {md_file.relative_to(docs_dir.parent)}")
                file_map[slug] = abs_path
                # print(f"    Mapped slug '{slug}' -> {md_file.relative_to(docs_dir.parent)}")

            # Use id if slug is not present and id is
            elif fm_id:
                 if fm_id in file_map:
                      print(f"  [WARN] Duplicate id '{fm_id}' found. Overwriting mapping for {md_file.relative_to(docs_dir.parent)}")
                 file_map[fm_id] = abs_path
                 # print(f"    Mapped id '{fm_id}' -> {md_file.relative_to(docs_dir.parent)}")

            # Fallback: Use the file path relative to docs dir (without extension) as a key
            rel_path_key = str(md_file.relative_to(docs_dir).with_suffix('')).replace(os.sep, '/')
            if rel_path_key not in file_map:
                 file_map[rel_path_key] = abs_path
                 # print(f"    Mapped path '{rel_path_key}' -> {md_file.relative_to(docs_dir.parent)}")


        except Exception as e:
            print(f"  [ERROR] Failed to read/process front matter for {md_file}: {e}")

    print(f"Scanned {count} files. Found {len(file_map)} potential mappings (slugs/IDs/paths).")
    # print(f"  [DEBUG] File map: {file_map}")
    return file_map


# --- Function to parse sidebars (remains mostly the same, used as fallback/supplement) ---
def parse_sidebars_to_map(sidebar_content):
    """
    Parses the sidebar JS content to extract a mapping from Docusaurus IDs/paths
    to their potential file paths relative to the docs root.
    Uses regex as a primary method, attempts JSON-like extraction as fallback.
    """
    mapping = {}
    # Regex to find strings like "Category/File" or 'Category/File' or object IDs
    # Covers: "id", 'id', id: "path", id: 'path'
    # Looks for strings containing at least one '/' or alphanumeric chars only
    id_regex = re.compile(r"""
        (?:id:\s*|type:\s*['"]doc['"]\s*,\s*id:\s*) # Optional id key or type:'doc',id:
        ['"]((?:[A-Za-z0-9_-]+/?)+)['"] # Capture the path-like string in quotes
    """, re.VERBOSE)

    matches = id_regex.findall(sidebar_content)
    for potential_id in matches:
        # Basic validation: should not be empty and likely contains letters/numbers/-/_/
        if potential_id and not potential_id.startswith(('http', '/api', '#')) and potential_id != 'docs':
             # Map the ID to itself (representing path relative to docs root)
             # We'll add .md/.mdx later during file finding
             mapping[potential_id] = potential_id
             # Also map the version without potential leading/trailing slashes if different
             cleaned_id = potential_id.strip('/')
             if cleaned_id != potential_id:
                  mapping[cleaned_id] = cleaned_id


    # Fallback attempt: Try to find simple string entries in arrays
    string_regex = re.compile(r"""
        (?:items:\s*\[[^\]]*?|\[\s*) # Start of an array (items: [ or just [)
        ['"]([A-Za-z0-9_-]+/[A-Za-z0-9_/-]+)['"] # Capture path-like string in quotes
    """, re.VERBOSE | re.DOTALL)
    string_matches = string_regex.findall(sidebar_content)
    for potential_id in string_matches:
         if potential_id and potential_id not in mapping and not potential_id.startswith(('http', '/api', '#')):
              mapping[potential_id] = potential_id
              cleaned_id = potential_id.strip('/')
              if cleaned_id != potential_id:
                   mapping[cleaned_id] = cleaned_id

    print(f"  [INFO] Extracted {len(mapping)} potential ID mappings from sidebars.")
    # print(f"  [DEBUG] Sidebar mapping: {mapping}") # Optional: for debugging
    return mapping

# --- Existing functions (calculate_relative_path, find_target_file) remain the same ---

def calculate_relative_path(source_file_path: pathlib.Path, target_file_path: pathlib.Path):
    """Calculates the relative path from the source file's directory to the target file path."""
    source_dir = source_file_path.parent
    try:
        # Calculate relative path using pathlib
        relative_path = os.path.relpath(target_file_path.resolve(), start=source_dir.resolve())

        # Handle case where source and target resolve to the same file
        if relative_path == '.':
            # Return the filename itself
            return target_file_path.name

        # Ensure forward slashes for web/markdown compatibility
        return str(pathlib.Path(relative_path)).replace(os.sep, '/')
    except ValueError as e:
        # This can happen if source and target are on different drives on Windows,
        # or other path resolution issues.
        print(f"  [WARN] Could not calculate relative path for target '{target_file_path}' from '{source_file_path}': {e}")
        return None


def find_target_file(start_dir: pathlib.Path, link_path_part: str, base_dir: pathlib.Path):
    """
    Tries to find the actual target file relative to start_dir, checking for .md and .mdx extensions.
    Ensures the found file is within the base_dir.
    """
    # Normalize the link path part to handle potential './' or extra slashes, but keep relative structure
    # Important: Don't normalize if it's empty or just '/'
    if not link_path_part or link_path_part == '/':
         return None
    normalized_link_path = pathlib.Path(link_path_part)

    potential_targets = [
        start_dir / normalized_link_path,
        start_dir / f"{normalized_link_path}.md",
        start_dir / f"{normalized_link_path}.mdx",
        # Also check if the link itself had the extension
        start_dir / normalized_link_path.with_suffix(".md"),
        start_dir / normalized_link_path.with_suffix(".mdx"),
    ]

    for potential_target in potential_targets:
        # Resolve the path to handle '..' etc.
        try:
            # Check existence before resolving to avoid errors on invalid paths
            if not potential_target.exists():
                continue
            resolved_target = potential_target.resolve()
        except OSError as e: # Handle potential errors during resolution (e.g., invalid chars)
             # print(f"    [DEBUG] Could not resolve potential target {potential_target}: {e}")
             continue


        if resolved_target.is_file(): # No need to check exists() again
            # Security/sanity check: Ensure the resolved path is within the base_dir
            try:
                resolved_target.relative_to(base_dir.resolve())
                # print(f"    [DEBUG] Found target: {resolved_target}")
                return resolved_target
            except ValueError:
                # print(f"    [DEBUG] Resolved target {resolved_target} outside base_dir {base_dir.resolve()}")
                continue # Resolved path is outside the base directory

    # print(f"    [DEBUG] Target not found for '{link_path_part}' relative to '{start_dir}'")
    return None


# --- Update process_markdown_file ---
def process_markdown_file(file_path: pathlib.Path, base_dir: pathlib.Path, sidebar_map: dict, file_slug_map: dict):
    """Processes a single markdown file to convert Docusaurus links to relative MkDocs links."""
    print(f"Processing: {file_path.relative_to(pathlib.Path.cwd())}")
    content_changed = False
    try:
        original_content = file_path.read_text(encoding='utf-8')
        content = original_content
        link_regex = re.compile(r'\[([^\]]+?)\]\(([^)]+)\)')
        current_file_abs_path = file_path.resolve()
        current_dir_abs_path = current_file_abs_path.parent
        base_dir_abs_path = base_dir.resolve()

        matches = list(link_regex.finditer(content))
        for match in reversed(matches):
            original_url = match.group(2)
            url = original_url.strip()

            # Ignore external links, mailto, tel, anchor-only links, empty links
            if url.startswith(('http://', 'https://', 'mailto:', 'tel:', '#')) or not url:
                continue

            anchor = ''
            url_part = url
            if '#' in url:
                url_part, anchor_part = url.split('#', 1)
                anchor = '#' + anchor_part
                if not url_part: # Link was only an anchor
                    continue

            target_file = None
            new_url = None # Initialize new_url to None
            print_prefix = "[REPLACED]" # Default prefix

            # --- Target Resolution ---
            if url_part.startswith('/static/'):
                # Handle old absolute static links -> new relative assets links
                path_relative_to_assets = url_part[len('/static/'):]
                target_asset_path = (base_dir_abs_path / 'assets' / path_relative_to_assets).resolve()

                if target_asset_path.exists() and target_asset_path.is_file():
                    new_relative_path = calculate_relative_path(current_file_abs_path, target_asset_path)
                    if new_relative_path is not None:
                        new_url = new_relative_path + anchor # Keep original extension for assets
                        print_prefix = "[REPLACED STATIC]"
                    else:
                         print(f"  [WARN] Could not calculate relative path for static asset: {target_asset_path}")
                else:
                    print(f"  [WARN] Static asset target not found at new location: {target_asset_path}")
                target_file = None # Handled as asset

            # --- Handle other common absolute asset paths ---
            elif any(url_part.startswith(prefix) for prefix in ['/img/', '/logos/', '/files/', '/videos/']):
                # Assumes these paths are relative to the original static root, now mapped to docs/assets
                path_relative_to_assets = url_part.lstrip('/') # e.g., img/playground-response.png
                target_asset_path = (base_dir_abs_path / 'assets' / path_relative_to_assets).resolve()

                if target_asset_path.exists() and target_asset_path.is_file():
                    new_relative_path = calculate_relative_path(current_file_abs_path, target_asset_path)
                    if new_relative_path is not None:
                        new_url = new_relative_path + anchor # Keep original extension
                        print_prefix = "[REPLACED ASSET]"
                    else:
                        print(f"  [WARN] Could not calculate relative path for asset: {target_asset_path}")
                else:
                    print(f"  [WARN] Asset target not found at new location: {target_asset_path}")
                target_file = None # Handled as asset

            # --- Handle other common absolute asset paths ---
            elif any(url_part.startswith(prefix) for prefix in ['/img/', '/logos/', '/files/', '/videos/']):
                # Assumes these paths are relative to the original static root, now mapped to docs/assets
                path_relative_to_assets = url_part.lstrip('/') # e.g., img/playground-response.png
                target_asset_path = (base_dir_abs_path / 'assets' / path_relative_to_assets).resolve()

                if target_asset_path.exists() and target_asset_path.is_file():
                    new_relative_path = calculate_relative_path(current_file_abs_path, target_asset_path)
                    if new_relative_path is not None:
                        new_url = new_relative_path + anchor # Keep original extension
                        print_prefix = "[REPLACED ASSET]"
                    else:
                        print(f"  [WARN] Could not calculate relative path for asset: {target_asset_path}")
                else:
                    print(f"  [WARN] Asset target not found at new location: {target_asset_path}")
                target_file = None # Handled as asset

            # --- Handle other common absolute asset paths ---
            elif any(url_part.startswith(prefix) for prefix in ['/img/', '/logos/', '/files/', '/videos/']):
                # Assumes these paths are relative to the original static root, now mapped to docs/assets
                path_relative_to_assets = url_part.lstrip('/') # e.g., img/playground-response.png
                target_asset_path = (base_dir_abs_path / 'assets' / path_relative_to_assets).resolve()

                if target_asset_path.exists() and target_asset_path.is_file():
                    new_relative_path = calculate_relative_path(current_file_abs_path, target_asset_path)
                    if new_relative_path is not None:
                        new_url = new_relative_path + anchor # Keep original extension
                        print_prefix = "[REPLACED ASSET]"
                    else:
                        print(f"  [WARN] Could not calculate relative path for asset: {target_asset_path}")
                else:
                    print(f"  [WARN] Asset target not found at new location: {target_asset_path}")
                target_file = None # Handled as asset

            elif url_part.startswith('/'):
                # Absolute path (non-static): Prioritize file_slug_map, then sidebar_map
                potential_id = url_part.lstrip('/')
                target_file_path_from_map = file_slug_map.get(potential_id) # Check slug/id map first

                if target_file_path_from_map:
                     # Found in file map (slug/id/path)
                     target_file = target_file_path_from_map # Already an absolute Path object
                     print_prefix = "[REPLACED SLUG/ID]"
                else:
                    # Not in file map, try sidebar map
                    mapped_path_part = sidebar_map.get(potential_id)
                    if mapped_path_part:
                         # Found in sidebar map, try finding file relative to base_dir using mapped path
                         target_file = find_target_file(base_dir_abs_path, mapped_path_part, base_dir_abs_path)
                         if target_file:
                              print_prefix = "[REPLACED MAPPED]"
                         else:
                              # Mapped path didn't resolve, fallback to direct path check
                              print(f"  [INFO] Sidebar mapped path '{mapped_path_part}' for link '{original_url}' did not resolve. Falling back.")
                              target_file = find_target_file(base_dir_abs_path, potential_id, base_dir_abs_path)
                              if target_file:
                                   print_prefix = "[REPLACED ABS DIRECT]"

                    elif not potential_id: # Handle the case where the link was just "/"
                         print(f"  [INFO] Skipping root link: '{original_url}'")
                         target_file = None
                         new_url = original_url # Keep original link if it was just "/"
                         print_prefix = "[INFO ROOT]"
                    else:
                        # Not in file map or sidebar map, try finding file directly relative to base_dir
                        target_file = find_target_file(base_dir_abs_path, potential_id, base_dir_abs_path)
                        if target_file:
                             print_prefix = "[REPLACED ABS DIRECT]"

                # If still not found as markdown/mdx, check if it's an asset linked absolutely
                if target_file is None and new_url is None and potential_id: # Check new_url to avoid re-checking root link
                    potential_asset_path = (base_dir_abs_path / potential_id).resolve()
                    if potential_asset_path.exists() and potential_asset_path.is_file() and potential_asset_path.suffix not in ['.md', '.mdx']:
                        new_relative_path = calculate_relative_path(current_file_abs_path, potential_asset_path)
                        if new_relative_path is not None:
                            new_url = new_relative_path + anchor
                            print_prefix = "[REPLACED ABS ASSET]"
                        else:
                            print(f"  [WARN] Could not calculate relative path for absolute asset: {potential_asset_path}")
                        # No need to set target_file = None, it's already None

            else:
                # Relative path: try relative to current_dir first
                target_file = find_target_file(current_dir_abs_path, url_part, base_dir_abs_path)
                if target_file:
                     print_prefix = "[REPLACED REL]"
                # If not found relative to current, maybe it's implicitly relative to base_dir?
                if not target_file:
                     target_file = find_target_file(base_dir_abs_path, url_part, base_dir_abs_path)
                     if target_file:
                          print_prefix = "[REPLACED BASE REL]"


            # --- Path Calculation and Replacement ---
            final_new_url = None # URL to actually use for replacement

            if target_file: # Found a markdown file (.md or .mdx)
                new_relative_path = calculate_relative_path(current_file_abs_path, target_file)
                if new_relative_path is not None:
                    # Ensure the final link uses .md extension
                    final_link_path = str(pathlib.Path(new_relative_path).with_suffix('.md'))
                    final_new_url = final_link_path + anchor
                    # print_prefix is already set based on how target_file was found
                # else: warning already printed

            elif new_url: # Asset link already calculated (e.g., /static/ or absolute asset)
                 final_new_url = new_url
                 # print_prefix is already set

            # --- Handle Directory Links (pointing to index files) if not already handled ---
            if final_new_url is None: # Only check for dirs if we haven't already found a target or calculated an asset URL
                potential_dir = None
                # Check relative to current first, then relative to base for dirs
                potential_dir_rel = (current_dir_abs_path / url_part).resolve()
                potential_dir_abs = (base_dir_abs_path / url_part.lstrip('/')).resolve() if url_part.startswith('/') else None

                if potential_dir_rel.is_dir():
                    potential_dir = potential_dir_rel
                elif potential_dir_abs and potential_dir_abs.is_dir():
                    potential_dir = potential_dir_abs

                if potential_dir and potential_dir.is_dir():
                    # Try finding index.md or index.mdx inside this directory
                    index_target = find_target_file(potential_dir, 'index', base_dir_abs_path)
                    if index_target:
                        new_relative_path = calculate_relative_path(current_file_abs_path, index_target)
                        if new_relative_path is not None:
                            final_link_path = str(pathlib.Path(new_relative_path).with_suffix('.md'))
                            final_new_url = final_link_path + anchor
                            print_prefix = "[REPLACED DIR]"
                        # else: warning already printed
                    else:
                         # Check if it's the base directory itself (e.g., link to '/')
                         if potential_dir == base_dir_abs_path:
                              # print(f"  [INFO] Link '{original_url}' points to the documentation root directory.")
                              # Keep original link for root? Or maybe point to index.md? Let's keep original for now.
                              final_new_url = original_url # Keep it as is
                              print_prefix = "[INFO ROOT]"
                         else:
                              print(f"  [WARN] Directory link '{original_url}' found, but no index.md/index.mdx inside.")

            # --- Perform Replacement if URL changed ---
            if final_new_url is not None and original_url != final_new_url:
                 start, end = match.span(2)
                 content = content[:start] + final_new_url + content[end:]
                 content_changed = True
                 # Use the determined prefix for clarity
                 print(f"  {print_prefix} '{original_url}' -> '{final_new_url}'")

            # --- Final Warning for Unresolved Links ---
            elif final_new_url is None: # Only warn if we didn't find *any* valid target or replacement
                 # Only warn if it doesn't look like a known static asset path pattern (using new 'assets' path)
                 # or other common file types that might be intentionally linked without .md
                 asset_patterns = ['/assets/', '/img/', '/logos/', '/videos/', '/files/', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.mp4', '.json', '.zip', '.pdf']
                 # Check if original_url contains any asset patterns
                 is_likely_asset = any(part.lower() in original_url.lower() for part in asset_patterns)
                 # Check if it looks like an anchor link within the same page
                 is_anchor_link = original_url.startswith('#')

                 if not is_likely_asset and not is_anchor_link:
                      print(f"  [WARN] Target not found for link: '{original_url}'")


        # --- Write Changes ---
        if content_changed:
            try:
                file_path.write_text(content, encoding='utf-8', errors='replace')
                print(f"  [SAVED] Changes to {file_path.relative_to(pathlib.Path.cwd())}")
            except Exception as write_e:
                print(f"  [ERROR] Failed to write changes to file {file_path}: {write_e}")

    except Exception as e:
        print(f"  [ERROR] Failed to process file {file_path}: {e}")
        traceback.print_exc()


def rename_mdx_to_md(directory: pathlib.Path):
    """Renames all .mdx files to .md recursively in the given directory."""
    renamed_files_count = 0
    path = pathlib.Path(directory).resolve() # Ensure we work with absolute paths
    mdx_files = sorted(list(path.rglob('*.mdx')), reverse=True)
    print(f"Found {len(mdx_files)} .mdx files to potentially rename.")

    for file_path in mdx_files:
        new_path = file_path.with_suffix('.md')
        if new_path.exists():
            print(f"  [SKIP RENAME] Target '{new_path.relative_to(pathlib.Path.cwd())}' already exists. Skipping rename of '{file_path.relative_to(pathlib.Path.cwd())}'.")
            continue
        try:
            shutil.move(str(file_path), str(new_path))
            print(f"  [RENAMED] {file_path.relative_to(pathlib.Path.cwd())} -> {new_path.relative_to(pathlib.Path.cwd())}")
            renamed_files_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to rename file {file_path} to {new_path}: {e}")
    print(f"Successfully renamed {renamed_files_count} files.")


# --- Update main ---
def main():
    docs_dir_name = 'docs'
    project_root = pathlib.Path.cwd()
    docs_path = project_root / docs_dir_name
    # Read sidebars.js from the project root
    original_sidebars_path = project_root / "sidebars.js"

    if not docs_path.is_dir():
        print(f"Error: Directory '{docs_dir_name}' not found in the current working directory ({project_root}).")
        return

    # --- Build map from front matter ---
    file_slug_map = build_file_map(docs_path)

    # --- Read and parse original sidebars.js (as fallback/supplement) ---
    sidebar_map = {}
    if original_sidebars_path.exists():
        print(f"Reading original sidebars config from: {original_sidebars_path}")
        try:
            sidebar_content = original_sidebars_path.read_text(encoding='utf-8')
            # Merge sidebar map into file_slug_map, prioritizing file_slug_map
            sidebar_map_parsed = parse_sidebars_to_map(sidebar_content)
            for key, value in sidebar_map_parsed.items():
                 if key not in file_slug_map: # Only add if not already mapped by front matter
                      sidebar_map[key] = value # Keep sidebar map separate for now for clarity in processing logic
        except Exception as e:
            print(f"  [ERROR] Failed to read or parse sidebars.js: {e}")
            print("Proceeding without sidebar mapping. Absolute links might not resolve correctly.")
    else:
        print(f"Warning: Original sidebars file not found at {original_sidebars_path}. Cannot use ID mapping.")


    print(f"\nStarting link conversion in directory: {docs_path.resolve()}")
    print(f"Project root considered: {project_root.resolve()}")

    # --- Phase 1: Process Content ---
    markdown_files = list(docs_path.rglob('*.md')) + list(docs_path.rglob('*.mdx'))
    print(f"\nFound {len(markdown_files)} markdown files to process for link conversion.")

    for file_path in markdown_files:
        process_markdown_file(file_path, docs_path, sidebar_map, file_slug_map) # Pass both maps

    # --- Phase 2: Rename Files ---
    print("\nStarting file renaming phase (.mdx -> .md)...")
    rename_mdx_to_md(docs_path)

    print("\nLink conversion and renaming process completed.")

if __name__ == "__main__":
    main()

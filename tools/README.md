# CodeKite Tools

This directory contains tools that support the CodeKite development workflow.

## Kit-to-CodeKite Integration Pipeline

### Background

CodeKite (this project) was originally forked from Kit, but the two codebases now exist as separate repositories with independent development paths:

- **Kit**: The original codebase, continuing its own development
- **CodeKite**: This repository, with its own direction and feature set

While the codebases have diverged, valuable features and improvements continue to be developed in Kit that would benefit CodeKite.

### Integration Pipeline

We've established a controlled, selective pipeline for integrating changes from Kit into CodeKite. This approach:

1. Maintains complete independence between the codebases
2. Gives us full control over which changes to adopt
3. Allows us to adapt changes to fit our architecture
4. Preserves our namespace and project conventions

### Pipeline Tools

#### `fetch_commit.py`

This tool extracts files from specified Kit commits while maintaining their directory structure:

```python
python tools/fetch_commit.py shaneholloman/kit <commit-hash>
```

The tool:

- Places files in `tmp-commits/<repo>-<commit-short>-<timestamp>/`
- Preserves original directory structure
- Creates a manifest of all downloaded files
- Isolates changes for review

### Integration Workflow

1. **Identify**: Find valuable commits or features in Kit
2. **Extract**: Use `fetch_commit.py` to download the relevant files - note: we are here in the process
3. **Review**: Examine the changes in isolation
4. **Adapt**: Convert to CodeKite's patterns:
   - Rename namespace from `kit` to `codekite`
   - Verify compatibility with our codebase
   - Ensure code meets our standards via linters
5. **Integrate**: Copy adapted files into CodeKite's structure
6. **Test**: Verify functionality works within our codebase
7. **Commit**: Add the changes to CodeKite with appropriate attribution

### Benefits

This approach allows CodeKite to:

- Evolve independently with complete autonomy
- Cherry-pick valuable features from Kit
- Maintain consistent code style and standards
- Integrate changes at our own pace
- Ensure changes fit our architectural patterns

### Future Enhancements

The pipeline can be improved with additional tools:

- Automated namespace conversion
- Integration test framework
- Change history tracking
- Compatibility analysis

### Usage Examples

Extract a specific commit:

```python
python tools/fetch_commit.py shaneholloman/kit ddafb6b3042284baba79fac0a370d91ede43f52d
```

Extract to a custom directory:

```python
python tools/fetch_commit.py shaneholloman/kit ddafb6b3042284baba79fac0a370d91ede43f52d --output-dir custom-dir
```

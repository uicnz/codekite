# CodeKite and CodeMapper Integration Plan

## Overview

This document outlines a plan to integrate the [CodeMapper](https://github.com/shaneholloman/codemapper) repository into CodeKite. While CodeKite is a Code Intelligence Agent focused on code analysis and context generation, CodeMapper specializes in generating comprehensive documentation of code structures in multiple formats (Markdown, XML, JSON, YAML, etc.). Combining these projects would enhance CodeKite's capabilities, allowing it to not only understand code but also generate human-readable and machine-readable documentation in various formats.

The integration plan follows the natural evolution path of both tools, as they were developed by the same author with complementary capabilities in mind, making their combination a logical next step in creating a more comprehensive Code Intelligence Agent.

## CodeMapper Analysis

### Purpose and Functionality

CodeMapper is a tool for generating comprehensive documentation artifacts of directory structures and file contents. It can:

1. Create detailed code maps of directories or GitHub repositories
2. Generate documentation maps focusing on README files and documentation directories
3. Handle .gitignore rules for file inclusion/exclusion
4. Apply intelligent code fence detection based on file extensions
5. Identify and appropriately handle large binary files

### Planned Features

According to the [roadmap](https://github.com/shaneholloman/codemapper/blob/main/docs/todo.md), CodeMapper plans to expand with:

1. **Multiple Output Formats**
   - Currently supports Markdown
   - Planned: XML, JSON, YAML, RST, AsciiDoc

2. **Expanded Git Support**
   - Additional Git hosting services (GitLab, Bitbucket)
   - Branch selection capabilities
   - Intelligent repository categorization

3. **AI Integration**
   - AI-generated code summarization
   - AI-generated alt text for images
   - Repository categorization

4. **Service Capabilities**
   - Server version with API
   - User authentication and authorization

5. **Visualization**
   - Mermaid flow chart generation for code execution visualization
   - Enhanced table of contents

6. **LLMs Integration**
   - LLMs.txt generation (similar to robots.txt for AI assistants)

### Core Components

1. **`config.py`**: Configuration settings and constants
   - Contains `BaseMapConfig` class for mapping configuration
   - Defines language mappings for code fences
   - Lists excluded file types and extensions

2. **`utils.py`**: Core utility functions
   - File reading and processing logic
   - GitHub repository cloning
   - Tree structure generation for Markdown output

3. **`main.py`**: Entry point and CLI handling
   - Command-line argument parsing
   - Workflow orchestration
   - Input type detection (local directory vs GitHub repository)

4. **`docmap.py`**: Documentation mapping module
   - Specialized functionality for documentation discovery
   - Structured documentation organization

## Integration Approach

### 1. Directory Structure Integration

Integrate CodeMapper into the planned CodeKite `tools/` directory structure:

```
src/codekite/
├── __init__.py
├── api/
│   ├── __init__.py
│   └── app.py
├── cli.py
├── mcp/
│   ├── __init__.py
│   ├── api_client.py
│   └── server.py
└── tools/
    ├── __init__.py
    ├── code_searcher.py
    ├── context_extractor.py
    ├── ...
    └── codemapper/
        ├── __init__.py
        ├── config.py
        ├── docmap.py
        ├── utils.py
        └── core.py  # Renamed from main.py to avoid confusion
```

### 2. Functionality Integration

#### Core CodeKite Integration

1. **Repository Integration**
   - Enhance `Repository` class to include code mapping capabilities
   - Add methods like `generate_code_map()` and `generate_doc_map()`

2. **CLI Integration**
   - Add CodeMapper commands to CodeKite CLI
   - Preserve existing CodeMapper CLI functionality

#### MCP Server Integration

Add new MCP tools to expose CodeMapper functionality:

1. **Tools**
   - `codekite_generate_codemap`: Generate code structure map in multiple formats (Markdown, XML, JSON, YAML)
   - `codekite_generate_docmap`: Generate documentation map in multiple formats
   - `codekite_get_map_formats`: List available map output formats
   - `codekite_generate_llms_txt`: Generate LLMs.txt for AI assistant guidance

2. **Resources**
   - `codekite://repository/{repo_id}/codemap`: Generated code map with format parameter
   - `codekite://repository/{repo_id}/docmap`: Generated doc map with format parameter

#### REST API Integration

Add new REST API endpoints:

1. **Code Mapping Endpoints**
   - `POST /api/repositories/{repo_id}/maps/code`: Generate code map with format selection (Markdown, XML, JSON, YAML)
   - `POST /api/repositories/{repo_id}/maps/docs`: Generate doc map with format selection
   - `GET /api/repositories/{repo_id}/maps`: Get generated maps
   - `GET /api/repositories/{repo_id}/maps/formats`: List supported output formats
   - `POST /api/repositories/{repo_id}/maps/llms-txt`: Generate LLMs.txt for AI guidance

### 3. Code Adaptations

1. **Import Restructuring**
   - Update imports in CodeMapper files to reflect new module structure
   - Ensure backward compatibility with relative imports

2. **Class Refactoring**
   - Ensure `BaseMapConfig` complements existing CodeKite configuration objects
   - Integrate CodeMapper's configuration with CodeKite's configuration system

3. **Function Adaptations**
   - Refactor any functions that might collide with CodeKite functions
   - Add type hints where missing to maintain CodeKite's typing standards

### 4. CLI Unification

1. **Unified Command Structure**
   - Add CodeMapper commands under the `codekite` CLI
   - Example: `codekite map code` and `codekite map docs`

2. **Arguments Standardization**
   - Standardize argument naming across both tools
   - Ensure consistent parameter handling

### 5. Documentation Updates

1. **Update API Documentation**
   - Document new code mapping capabilities in API reference
   - Add examples of code mapping usage

2. **Create Integration Examples**
   - Provide examples of using code search with code mapping
   - Show how to generate context with included code maps

## Implementation Plan

### Phase 1: Basic Integration

1. Import CodeMapper files into the CodeKite project
2. Restructure imports and resolve any conflicts
3. Create simple wrapper functions to call CodeMapper functionality
4. Add basic CLI integration

### Phase 2: MCP and API Integration

1. Create MCP tools for code mapping
2. Implement REST API endpoints
3. Add resource handlers for generated maps
4. Create object model integration between CodeKite and CodeMapper

### Phase 3: Enhanced Integration

1. Improve code mapping to leverage CodeKite's deeper code understanding
2. Enhance documentation maps with semantic information from CodeKite
3. Optimize performance for large repositories
4. Implement caching for generated maps

## Benefits of Integration

1. **Enhanced Documentation Capabilities**
   - Generate human-readable code structure documentation in multiple formats (Markdown, XML, JSON, YAML)
   - Improve documentation discovery and organization
   - Support both human-readable and machine-readable output formats

2. **Better Context Generation**
   - Include structural information in AI context
   - Provide higher-level code organization understanding
   - Enable AI to work with code maps in preferred format

3. **Comprehensive Repository Analysis**
   - Combine semantic understanding with structural mapping
   - Provide both machine-oriented and human-oriented views of repositories
   - Generate standardized LLMs.txt files for AI assistant guidance

4. **Unified Interface**
   - Single API for code intelligence and documentation
   - Consistent experience across different code analysis needs
   - Format flexibility through parameterized outputs

## Potential Challenges

1. **Naming Conflicts**
   - Some function or class names might overlap
   - Solution: Use namespacing and clear module boundaries

2. **Configuration Differences**
   - CodeMapper and CodeKite might have different configuration approaches
   - Solution: Create adapter layer between configuration systems

3. **Performance Concerns**
   - Combined operations might impact performance
   - Solution: Implement caching and parallel processing where appropriate

## Conclusion

Integrating CodeMapper into CodeKite will significantly enhance the capabilities of the Code Intelligence Agent, adding powerful documentation generation capabilities to its existing code understanding features. This integration aligns with the vision of CodeKite as a comprehensive agent for code understanding and makes its capabilities more accessible to both humans and AI assistants.

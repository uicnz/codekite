# CodeKite REST API Parity Plan

## Overview

While CodeKite (Code Intelligence Agent) now has an MCP server implementation, a traditional REST API is also required for clients that don't support the MCP protocol. This document outlines a plan to create a comprehensive REST API with perfect parity across all three layers:

1. **Core CodeKite Functions** (Python library)
2. **MCP Server** (Tools and Resources)
3. **REST API** (HTTP endpoints)

The goal is to ensure that any capability available in the CodeKite library is equally accessible through both the MCP server and the REST API, providing consistent intelligence capabilities across all interfaces.

## Current Status

### Existing API Structure

The current API module located at `src/codekite/api/` provides a basic REST API implementation:

```sh
src/codekite/api/
├── __init__.py
└── app.py  # FastAPI implementation
```

However, this implementation does not fully cover all CodeKit capabilities, particularly the newer features and those identified as missing from the MCP server in the MCP expansion plan.

## API Design Principles

### 1. Resource-Oriented Architecture

The REST API should follow RESTful principles with resources that map directly to CodeKit concepts:

- Repositories
- Files
- Symbols (functions, classes)
- Search results
- Summaries
- Dependencies
- Context

### 2. Consistent Operation Patterns

The API will follow consistent patterns for operations:

- **GET** for retrieving resources
- **POST** for creating resources or performing operations
- **PUT** for updating resources
- **DELETE** for removing resources

### 3. Query Parameter Consistency

Query parameters will follow consistent naming conventions across all endpoints:

- `repo_id` for repository identifiers
- `path` for file paths
- `query` for search queries
- `limit` for result size limitations
- `offset` for pagination

### 4. Response Format Standardization

All API responses will follow a standard format:

```json
{
  "status": "success|error",
  "data": { /* response data */ },
  "metadata": { /* pagination, processing time, etc. */ },
  "error": { /* present only if status is error */ }
}
```

## API Endpoint Mapping

The following table shows how CodeKit functions and MCP tools/resources will map to REST API endpoints.

### Repository Operations

| CodeKit Function          | MCP Tool/Resource                           | REST API Endpoint                       | HTTP Method |
| ------------------------- | ------------------------------------------- | --------------------------------------- | ----------- |
| Repository initialization | `codekite_open_repository`                  | `/api/repositories`                     | POST        |
| Repository info           | `codekite://repository/{repo_id}/summary`   | `/api/repositories/{repo_id}`           | GET         |
| Repository structure      | `codekite://repository/{repo_id}/structure` | `/api/repositories/{repo_id}/structure` | GET         |
| File content              | Repository.get_file_content                 | `/api/repositories/{repo_id}/files`     | GET         |

### Code Search

| CodeKit Function | MCP Tool/Resource      | REST API Endpoint                               | HTTP Method |
| ---------------- | ---------------------- | ----------------------------------------------- | ----------- |
| Pattern search   | `codekite_search_code` | `/api/repositories/{repo_id}/search/pattern`    | GET         |
| Semantic search  | (To be added)          | `/api/repositories/{repo_id}/search/semantic`   | GET         |
| Symbol search    | (To be added)          | `/api/repositories/{repo_id}/search/symbols`    | GET         |
| Docstring search | (To be added)          | `/api/repositories/{repo_id}/search/docstrings` | GET         |

### Dependency Analysis

| CodeKit Function | MCP Tool/Resource | REST API Endpoint                                | HTTP Method |
| ---------------- | ----------------- | ------------------------------------------------ | ----------- |
| Get dependencies | (To be added)     | `/api/repositories/{repo_id}/dependencies`       | GET         |
| Analyze impact   | (To be added)     | `/api/repositories/{repo_id}/impact`             | POST        |
| Generate graph   | (To be added)     | `/api/repositories/{repo_id}/dependencies/graph` | GET         |

### Summarization

| CodeKit Function   | MCP Tool/Resource | REST API Endpoint                                                 | HTTP Method |
| ------------------ | ----------------- | ----------------------------------------------------------------- | ----------- |
| Summarize file     | (To be added)     | `/api/repositories/{repo_id}/summaries/files/{file_path}`         | GET         |
| Summarize function | (To be added)     | `/api/repositories/{repo_id}/summaries/functions/{function_path}` | GET         |
| Summarize class    | (To be added)     | `/api/repositories/{repo_id}/summaries/classes/{class_path}`      | GET         |

### Context Assembly

| CodeKit Function  | MCP Tool/Resource        | REST API Endpoint                               | HTTP Method |
| ----------------- | ------------------------ | ----------------------------------------------- | ----------- |
| Build context     | `codekite_build_context` | `/api/repositories/{repo_id}/context`           | POST        |
| Optimize context  | (To be added)            | `/api/repositories/{repo_id}/context/optimize`  | POST        |
| Context templates | (To be added)            | `/api/repositories/{repo_id}/context/templates` | GET/POST    |

## Implementation Plan

### Phase 1: Core Functionality

1. **Repository API**
   - Repository creation/opening
   - Repository structure retrieval
   - File content access

2. **Basic Search API**
   - Pattern-based code search endpoint
   - Symbol search endpoint

3. **Basic Context API**
   - Context building endpoint

### Phase 2: Advanced Features

1. **Advanced Search API**
   - Semantic search endpoint
   - Docstring search endpoint

2. **Dependency Analysis API**
   - Dependency graph endpoint
   - Impact analysis endpoint

3. **Summarization API**
   - File summary endpoint
   - Function/Class summary endpoint

### Phase 3: Optimization and Templates

1. **Context Optimization API**
   - Context optimization endpoint
   - Template management endpoints

2. **Advanced Configuration API**
   - Search configuration endpoints
   - Summarization configuration endpoints

## Technical Implementation

### FastAPI Integration

The API will be implemented using FastAPI for several reasons:

1. Fast performance
2. Automatic OpenAPI documentation
3. Type validation via Pydantic
4. Asynchronous support
5. Dependency injection

### Code Structure

The REST API code should be structured to maintain a clean separation of concerns:

```sh
src/codekite/api/
├── __init__.py
├── app.py                # Main FastAPI application
├── routes/               # Route definitions
│   ├── __init__.py
│   ├── repositories.py   # Repository endpoints
│   ├── search.py         # Search endpoints
│   ├── dependencies.py   # Dependency analysis endpoints
│   ├── summaries.py      # Summarization endpoints
│   └── context.py        # Context assembly endpoints
├── models/               # Pydantic models
│   ├── __init__.py
│   ├── repositories.py
│   ├── search.py
│   ├── dependencies.py
│   ├── summaries.py
│   └── context.py
└── services/             # Business logic
    ├── __init__.py
    └── adapter.py        # Adapts CodeKit functions to API operations
```

### Authentication and Authorization

The API should support:

1. API key authentication
2. Optional OAuth2 integration
3. Role-based access control for multi-user scenarios

### Rate Limiting and Caching

To ensure API performance:

1. Implement rate limiting for public access
2. Add result caching for expensive operations
3. Add ETag support for efficient cache validation

## Testing Strategy

### 1. Unit Tests

Create unit tests for:

- Input validation
- Response formatting
- Error handling

### 2. Integration Tests

Create integration tests for:

- End-to-end API flows
- Multi-step workflows

### 3. Parity Tests

Create special tests to verify parity between:

- CodeKit function results vs. REST API results
- MCP server results vs. REST API results

## Documentation

### 1. OpenAPI Specification

Leverage FastAPI's automatic OpenAPI generation:

- Complete schema documentation
- Example requests and responses
- Authentication details

### 2. API Reference Guide

Create a comprehensive API reference guide:

- Endpoint descriptions
- Parameter details
- Response format examples
- Error code explanations

### 3. Usage Examples

Provide usage examples for common scenarios:

- Repository analysis
- Code search
- Context building

## Deployment Considerations

### 1. API Versioning

Implement API versioning from the start:

- URL-based versioning (e.g., `/api/v1/...`)
- Version header support

### 2. Health Monitoring

Add health check endpoints:

- Basic server health (`/health`)
- Dependency health (`/health/dependencies`)

### 3. Performance Monitoring

Add performance monitoring:

- Request duration tracking
- Error rate monitoring
- Resource usage statistics

## Implementation Roadmap

1. **API Design Review** (1 week)
   - Finalize endpoint specifications
   - Define request/response models

2. **Core Implementation** (2-3 weeks)
   - Implement Phase 1 endpoints
   - Add authentication and basic security

3. **Advanced Features** (3-4 weeks)
   - Implement Phase 2 & 3 endpoints
   - Add rate limiting and caching

4. **Testing and Documentation** (2 weeks)
   - Complete test suite
   - Finalize API documentation

## Success Criteria

The REST API implementation will be considered successful when:

1. All CodeKit functions are accessible via REST endpoints
2. All MCP tools and resources have equivalent REST endpoints
3. Test coverage is >90% for API code
4. Documentation is complete and accurate
5. Performance benchmarks meet target requirements

## Conclusion

Implementing a complete REST API with perfect parity to both CodeKit functions and the MCP server will provide a comprehensive and flexible interface for all clients. This plan outlines a phased approach to ensure all functionality is exposed in a consistent, well-documented API that adheres to REST best practices.

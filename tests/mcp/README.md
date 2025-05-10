# CodeKite MCP Tests

This directory contains interactive tests for the CodeKite Model Context Protocol (MCP) server and client. These tests are primarily designed for developer use, manual verification, and demonstrations.

## Test Files Overview

The tests are organized following a pattern-based naming convention: `test_mcp_[component]_[variant].py`

| Filename                        | Purpose                                    | Server Port | Notes                              |
| ------------------------------- | ------------------------------------------ | ----------- | ---------------------------------- |
| `test_mcp_basic.py`             | Basic functionality test with debug output | 8000        | Simple test for quick verification |
| `test_mcp_client.py`            | Client API functionality test              | 8000        | Focuses on client API behavior     |
| `test_mcp_server.py`            | Automated testing framework                | 8000        | Currently uses existing server     |
| `test_mcp_server_live.py`       | Testing with pre-running server            | 8001        | Clean output, best for demos       |
| `test_mcp_server_standalone.py` | Standalone server mode test                | 8000        | Verbose debug output               |

## Running the Tests

### Automated Testing Framework

The `test_mcp_server.py` test is designed for CI/CD frameworks, but currently uses an existing server on port 8000:

```bash
python tests/mcp/test_mcp_server.py
```

This test contains the framework for automated server startup/shutdown but is currently simplified to use an existing server. Before running this test, make sure you have a server running on port 8000.

### Live Server Tests

For other tests, you need to start the MCP server first in a separate terminal:

```bash
# For test_mcp_server_live.py (port 8001)
python -c "from codekite.cli import app; app(['mcp-serve', '--transport', 'streamable-http', '--port', '8001', '--asgi', '--log-level', 'debug'])"

# For other tests (port 8000)
python -c "from codekite.cli import app; app(['mcp-serve', '--transport', 'streamable-http', '--port', '8000', '--asgi', '--log-level', 'debug'])"
```

Then in another terminal, run the specific test:

```bash
python tests/mcp/test_mcp_server_live.py
# or
python tests/mcp/test_mcp_basic.py
# etc.
```

## Test Features

Each test validates the core MCP functionality:

1. Server connection and availability
2. Tool discovery
3. Repository opening
4. Code searching
5. Structure resource access
6. Summary resource access

The tests differ in their output verbosity, error handling, and setup/teardown processes.

## Human-Oriented Testing

These tests are specifically designed for interactive use by developers rather than automated CI/CD systems:

- They provide human-readable output with descriptive messages
- Most require manual server startup and configuration
- They display formatted JSON results for visual inspection
- They're optimized for different debugging and demonstration scenarios
- They contain detailed debug information to help diagnose issues

While `test_mcp_server.py` is intended to eventually support CI/CD environments, the current implementation of all tests is oriented toward human interaction.

## Choosing the Right Test

- **For CI/CD**: Use `test_mcp_server.py` once it's updated to run in a truly self-contained mode
- **For demos/presentations**: Use `test_mcp_server_live.py` as it has clean, formatted output
- **For debugging issues**: Use `test_mcp_server_standalone.py` for its verbose debug output
- **For quick verification**: Use `test_mcp_basic.py` for a lightweight test
- **For client API verification**: Use `test_mcp_client.py` to focus on client functionality

## Common Issues

- **Port conflicts**: If port 8000/8001 is already in use, you'll need to modify the server startup command and the test file to use a different port.
- **Connection errors**: Ensure the server is running before executing the live server tests.
- **Resource errors**: Most tests assume they're run from the project root directory. Use `cd /path/to/codekit` before running tests.

# Development guide

This guide provides comprehensive instructions for setting up, developing, and deploying the DataRobot MCP (Model Context Protocol) Server.

## Table of contents

- [Prerequisites](#prerequisites)
- [Initial setup](#initial-setup)
- [Running the server](#running-the-server)
- [Development workflow](#development-workflow)
  - [MCP client configuration](#mcp-client-configuration)
  - [OpenTelemetry configuration](#opentelemetry-configuration)
  - [Dynamic tool registration](#dynamic-tool-registration)
  - [Dynamic prompt registration](#dynamic-prompt-registration)
- [Code quality](#code-quality)
- [Testing](#testing)
- [Debugging](#debugging)

## Prerequisites

Before you begin, make sure you have the following:

- **uv**: Python package installer and project manager
- **DataRobot account**: An active DataRobot account with API credentials
- **Python 3.11+**: Required Python version

## Initial setup

### 1. Install uv

If you haven't already installed `uv`, run the following command:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For alternative installation methods, refer to the [uv documentation](https://github.com/astral-sh/uv).

### 2. Configure environment variables

Create a `.env` file in the application directory. You can copy it from `.env.template` in the same directory.

Then set the following variables:

#### Required variables

```bash
# DataRobot API credentials
DATAROBOT_API_TOKEN=your_api_token
DATAROBOT_ENDPOINT=your_datarobot_endpoint
```

#### Optional variables

```bash
# MCP server configuration
# MCP_SERVER_NAME=your_server_name
# MCP_SERVER_PORT=8080
# MCP_SERVER_LOG_LEVEL=DEBUG

# Dynamic tool registration
# MCP_SERVER_REGISTER_DYNAMIC_TOOLS_ON_STARTUP=true
# MCP_SERVER_TOOL_REGISTRATION_ALLOW_EMPTY_SCHEMA=true
# MCP_SERVER_TOOL_REGISTRATION_DUPLICATE_BEHAVIOR=warn

# Dynamic prompt registration
# MCP_SERVER_REGISTER_DYNAMIC_PROMPTS_ON_STARTUP=true
# MCP_SERVER_PROMPT_REGISTRATION_DUPLICATE_BEHAVIOR=warn

# Application configuration
# APP_LOG_LEVEL=DEBUG

# OpenTelemetry configuration
# OTEL_ENABLED=false
# OTEL_ENABLED_HTTP_INSTRUMENTORS=true
```

## Running the server

### Local development

To start the MCP server locally:

```bash
task dev
```

This command:

- Creates a virtual environment (if needed)
- Installs all dependencies
- Starts the MCP server on the configured port (default: 8080)

### Deploy to DataRobot

To deploy the MCP server to DataRobot:

```bash
task deploy
```

This will build and deploy the server as a DataRobot custom model application.

## Development workflow

### MCP client configuration

To use the MCP server with AI assistants, configure your MCP client to connect to it.
Replace placeholder values such as `YOUR_API_KEY` and `<deployment-id>` with your own values.
The local examples below use the default port, `8080`.

#### Cursor

Edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "datarobot-mcp-server": {
      "url": "http://localhost:8080/mcp/"
    },
    "datarobot-mcp-server-remote": {
      "url": "https://app.datarobot.com/deployments/<deployment-id>/directAccess/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY",
        "x-datarobot-api-key": "YOUR_API_KEY"
      }
    }
  }
}
```

#### VS Code

Edit `~/Library/Application Support/Code/User/mcp.json` (macOS) or `%APPDATA%\Code\User\mcp.json` (Windows):

```json
{
  "mcp": {
    "servers": {
      "datarobot-mcp-server": {
        "url": "http://localhost:8080/mcp/",
        "type": "http"
      }
    }
  }
}
```

For a deployed server, use a configuration such as:

```json
{
  "mcp": {
    "servers": {
      "datarobot-mcp-server-remote": {
        "url": "https://app.datarobot.com/deployments/<deployment-id>/directAccess/mcp/",
        "type": "http",
        "headers": {
          "Authorization": "Bearer YOUR_API_KEY",
          "x-datarobot-api-key": "YOUR_API_KEY"
        }
      }
    }
  }
}
```

#### Claude Desktop

1. Install Node.js. Claude Desktop uses the `mcp-remote` proxy for HTTP-based MCP servers:

```bash
brew install node
```

2. Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "datarobot-mcp-server": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote@latest",
        "https://app.datarobot.com/deployments/<deployment-id>/directAccess/mcp/",
        "--header",
        "Authorization: ${AUTH_HEADER}",
        "--transport",
        "http"
      ],
      "env": {
        "AUTH_HEADER": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

For more detailed client setup instructions, including local Claude Desktop examples, see the [MCP client setup guide](docs/mcp_client_setup.md).

### OpenTelemetry configuration

The server supports OpenTelemetry for distributed tracing and observability.

#### Key features

- **Automatic HTTP Client Instrumentation**: Supports aiohttp, httpx, and requests
- **Tool Execution Tracing**: Captures tool parameters and results
- **Error Tracking**: Monitors errors and status
- **Custom Attributes**: Support for custom tracing attributes

#### OpenTelemetry settings

Add the following environment variables to your `.env` file:

```bash
# Enable/disable OpenTelemetry (default: true)
OTEL_ENABLED=true
# Enable/disable HTTP instrumentors (default: false)
OTEL_ENABLED_HTTP_INSTRUMENTORS=false
```

### Dynamic tool registration

The server can automatically discover and register DataRobot deployments as MCP tools.

When enabled, the server scans for deployments tagged with `tool` and automatically registers each one as an MCP tool. This allows you to expose DataRobot models as tools without manual configuration.

For detailed information about this feature, including supported workflows and prerequisites, see the [Dynamic tool registration guide](docs/dynamic_tool_registration.md).

#### Tool registration settings

```bash
# Enable or disable dynamic tool registration on startup (default: false)
MCP_SERVER_REGISTER_DYNAMIC_TOOLS_ON_STARTUP=true

# Allow tools with empty schemas (default: false)
MCP_SERVER_TOOL_REGISTRATION_ALLOW_EMPTY_SCHEMA=true

# How to handle duplicate tools: 'error', 'warn', or 'ignore' (default: 'warn')
MCP_SERVER_TOOL_REGISTRATION_DUPLICATE_BEHAVIOR=warn
```

### Dynamic prompt registration

The server can automatically discover and register DataRobot prompts as MCP prompts.

#### Prompt registration settings

```bash
# Enable or disable dynamic prompt registration on startup (default: false)
MCP_SERVER_REGISTER_DYNAMIC_PROMPTS_ON_STARTUP=true

# How to handle duplicate prompts: 'error', 'warn', or 'ignore' (default: 'warn')
MCP_SERVER_PROMPT_REGISTRATION_DUPLICATE_BEHAVIOR=warn
```

## Code quality

Maintain code quality by running linting and formatting checks:

```bash
# Install dependencies and run linting/formatting
uv sync --all-extras && uv run ruff check --select I --fix && uv run ruff format
```

This command will:

- Install all dependencies including development extras
- Check import sorting and fix issues
- Format code according to project standards

## Testing

Run the test suite:

```bash
# Install dependencies and run tests
uv sync --all-extras && uv run pytest
```

For more testing options, run:

```bash
# Run tests with coverage
uv run pytest --cov

# Run a specific test file
uv run pytest app/tests/integration/test_user_tools.py

# Run tests with verbose output
uv run pytest -v
```

## Debugging

### Viewing logs

Monitor the MCP server logs to debug issues:

- **Local development**: Logs are output to the console where you ran `task dev`
- **Deployed server**: Check the DataRobot deployment logs in the DataRobot UI

### Common issues

1. **Connection errors**: Verify that the server is running and the URL is correct.
2. **Authentication failures**: Check that your `DATAROBOT_API_TOKEN` is valid.
3. **Tool registration issues**: Review the server logs for registration errors.
4. **Port conflicts**: Make sure the configured port (default: 8080) is available.

### Debug mode

Enable debug logging by setting:

```bash
MCP_SERVER_LOG_LEVEL=DEBUG
APP_LOG_LEVEL=DEBUG
```

This will provide detailed logging output for troubleshooting.

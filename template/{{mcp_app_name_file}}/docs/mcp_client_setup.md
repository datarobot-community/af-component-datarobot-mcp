# MCP client setup

This guide explains how to connect common MCP clients to your DataRobot MCP server during local development and after deployment to DataRobot.
It includes:

- Cursor, VS Code, and Claude Desktop setup
- local and deployed connection examples
- authentication guidance for DataRobot direct-access endpoints
- verification steps
- troubleshooting tips

## Table of contents

- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
  - [Cursor](#cursor)
  - [VS Code](#vs-code)
  - [Claude Desktop](#claude-desktop)
- [Use multiple environments](#use-multiple-environments)
- [Verify the connection](#verify-the-connection)
- [Troubleshooting](#troubleshooting)
- [Advanced features](#advanced-features)
- [Additional resources](#additional-resources)

## Prerequisites

Before you begin, make sure you have:

- A [running MCP server](../README.md#run-locally) (locally or deployed to DataRobot)
- Your [DataRobot API token](../README.md#add-api-credentials) (for remote connections)
- The [MCP endpoint URL](../README.md)

By default, this template serves MCP locally at `http://localhost:8080/mcp/`. If you set `MCP_SERVER_PORT`, replace `8080` in the examples below with your configured port.

For more information about DataRobot API keys, see the [DataRobot API keys documentation](https://docs.datarobot.com/en/docs/get-started/acct-mgmt/acct-settings/api-key-mgmt.html).

## Quick start

In the examples below, replace:

- `[YOUR_DATA_ROBOT_ENDPOINT]` with your DataRobot endpoint
- `[YOUR_DEPLOYMENT_ID]` with your deployment ID
- `[YOUR_DATA_ROBOT_API_KEY]` with your DataRobot API key

### Cursor

Edit `~/.cursor/mcp.json`.

#### Local MCP server

```json
{
  "mcpServers": {
    "datarobot-local": {
      "url": "http://localhost:8080/mcp/"
    }
  }
}
```

#### Deployed MCP server

```json
{
  "mcpServers": {
    "datarobot-production": {
      "url": "https://[YOUR_DATA_ROBOT_ENDPOINT]/deployments/[YOUR_DEPLOYMENT_ID]/directAccess/mcp/",
      "headers": {
        "Authorization": "Bearer [YOUR_DATA_ROBOT_API_KEY]",
        "x-datarobot-api-key": "[YOUR_DATA_ROBOT_API_KEY]"
      }
    }
  }
}
```

After you update the file:

1. Restart Cursor.
2. Ask the cursor AI "What MCP tools are available?"

### VS Code

Edit `~/Library/Application Support/Code/User/mcp.json` on macOS, `%APPDATA%\Code\User\mcp.json` on Windows, or the equivalent path on Linux.

#### Local MCP server

```json
{
  "mcp": {
    "servers": {
      "datarobot-local": {
        "url": "http://localhost:8080/mcp/",
        "type": "http"
      }
    }
  }
}
```

#### Deployed MCP server

```json
{
  "mcp": {
    "servers": {
      "datarobot-production": {
        "url": "https://[YOUR_DATA_ROBOT_ENDPOINT]/deployments/[YOUR_DEPLOYMENT_ID]/directAccess/mcp/",
        "type": "http",
        "headers": {
          "Authorization": "Bearer [YOUR_DATA_ROBOT_API_KEY]",
          "x-datarobot-api-key": "[YOUR_DATA_ROBOT_API_KEY]"
        }
      }
    }
  }
}
```

After you update the file:

1. Restart VS Code, or reload the window with `Cmd+Shift+P` -> `Developer: Reload Window`.
2. Open the Output panel and check the MCP-related output.

### Claude Desktop

Claude Desktop uses the `mcp-remote` proxy for HTTP-based MCP servers, so Node.js must be installed first.

1. Install Node.js if it is not already installed.

```bash
# macOS
brew install node

# Or download Node.js from https://nodejs.org/
```

2. Edit `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, or the equivalent path on your OS.

#### Local MCP server

```json
{
  "mcpServers": {
    "datarobot-local": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote@latest",
        "http://localhost:8080/mcp/",
        "--transport",
        "http"
      ]
    }
  }
}
```

#### Deployed MCP server

```json
{
  "mcpServers": {
    "datarobot-production": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote@latest",
        "https://[YOUR_DATA_ROBOT_ENDPOINT]/deployments/[YOUR_DEPLOYMENT_ID]/directAccess/mcp/",
        "--header",
        "Authorization: ${AUTH_HEADER}",
        "--transport",
        "http"
      ],
      "env": {
        "AUTH_HEADER": "Bearer [YOUR_DATA_ROBOT_API_KEY]"
      }
    }
  }
}
```

After you update the file:

1. Completely quit Claude Desktop.
2. Restart the application.
3. Ask the Claude Desktop AI "What tools do you have access to?"

## Use multiple environments (optional)

You can define multiple MCP servers in the same client configuration, such as local, staging, and production. This is useful when you want to test locally before switching to a deployed server.

*Example for Cursor*:

```json
{
  "mcpServers": {
    "local": {
      "url": "http://localhost:8080/mcp/"
    },
    "production": {
      "url": "https://[YOUR_DATA_ROBOT_ENDPOINT]/deployments/[YOUR_DEPLOYMENT_ID]/directAccess/mcp/",
      "headers": {
        "Authorization": "Bearer [YOUR_DATA_ROBOT_API_KEY]",
        "x-datarobot-api-key": "[YOUR_DATA_ROBOT_API_KEY]"
      }
    }
  }
}
```

## Verify the connection

After you configure your client, verify both the server and the client connection.

### Verify the server

1. Check that the server is running:

   ```bash
   curl http://localhost:8080/
   ```

   Expected result: a JSON health response, such as `{"status": "healthy", "message": "DataRobot MCP Server is running"}`.

2. Check the MCP endpoint:

   ```bash
   curl http://localhost:8080/mcp/
   ```

   Expected result: an MCP protocol response.

### Verify each client

#### Cursor

1. Open Cursor.
2. Open the Command Palette with `Cmd+Shift+P` on macOS or `Ctrl+Shift+P` on Windows and Linux.
3. Search for MCP-related commands.
4. Ask, "What MCP tools are available?"
5. Confirm that Cursor lists tools from your MCP server.

#### VS Code

1. Open VS Code.
2. Open `View -> Output`.
3. Select the MCP-related output, if available.
4. Look for successful connection messages.
5. Use an AI feature and ask about available tools.

#### Claude Desktop

1. Open Claude Desktop.
2. Review `~/Library/Logs/Claude/mcp*.log` on macOS, or the equivalent log path on your OS.
3. Look for a successful connection message.
4. Ask, "What tools do you have access to?"

## Troubleshooting

### Check client logs

If the connection test fails, review the client logs first:

- Cursor: `View -> Output`, then select `MCP Logs`
- VS Code: `View -> Output`, then select the MCP-related output
- Claude Desktop: `~/Library/Logs/Claude/mcp*.log`

### Server issues

If the server does not start:

```text
Port 8080 already in use?
  Yes -> stop the process using that port
  No  -> check dependencies and environment variables

Missing dependencies?
  Yes -> run `task install`
  No  -> review the startup logs

Invalid API token?
  Yes -> generate a new token in DataRobot
  No  -> check your `.env` file
```

If the server starts but returns errors:

- review the server logs for the exact error
- confirm that `DATAROBOT_API_TOKEN` is valid
- confirm that `DATAROBOT_ENDPOINT` is correct
- make sure the required environment variables are set

### Client connection issues

If the client cannot connect:

- make sure the server is running
- verify the configured URL
- confirm that the client was restarted after the config change
- check for firewall or network restrictions

Use these URL patterns:

- local: `http://localhost:8080/mcp/`
- deployed: `https://<your-endpoint>/deployments/<id>/directAccess/mcp/`

### Authentication issues

For DataRobot direct-access endpoints, use `Authorization: Bearer <token>`. For clients that support custom headers directly, also include `x-datarobot-api-key` with the same API key value.

If authentication fails:

- confirm that the API token is valid
- confirm that the `Bearer` header is formatted correctly
- confirm that the deployment ID is correct
- make sure your account has access to the deployment

### Claude Desktop issues

If Claude Desktop cannot launch `mcp-remote`:

- make sure Node.js is installed
- run `node --version`
- run `npx mcp-remote@latest --version`
- make sure `npx` is available in your `PATH`

### Quick diagnostic commands

Test your API token:

```bash
curl -H "Authorization: Bearer $DATAROBOT_API_TOKEN" \
  "$DATAROBOT_ENDPOINT/api/v2/projects/" | head -1
```

Check whether port 8080 is already in use:

```bash
lsof -i :8080
```

## Advanced features

Most users can skip this section. These settings are useful when you need advanced deployment or observability behavior.

### Dynamic tool registration

Use this feature when you want the MCP server to discover DataRobot deployments and register them as tools automatically.

```bash
MCP_SERVER_REGISTER_DYNAMIC_TOOLS_ON_STARTUP=true
```

For details, see the [dynamic tool registration guide](./dynamic_tool_registration.md).

### Dynamic prompt registration

Use this feature when you want the MCP server to discover DataRobot prompts and register them automatically.

```bash
MCP_SERVER_REGISTER_DYNAMIC_PROMPTS_ON_STARTUP=true
```

### OpenTelemetry tracing

Use this feature when you need distributed tracing for debugging or observability.

```bash
OTEL_ENABLED=true
OTEL_COLLECTOR_BASE_URL=https://your-otel-endpoint
OTEL_ENTITY_ID=your-entity-id
```

### Feature flag validation

If your deployment depends on specific DataRobot features, add feature flag files under `infra/feature_flags/` so deployment fails early when required capabilities are unavailable.

## Additional resources

- [FastMCP documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol specification](https://modelcontextprotocol.io/)
- [Cursor MCP documentation](https://docs.cursor.com/)
- [Claude Desktop documentation](https://www.anthropic.com/claude/desktop)
# MCP Server Development Instructions

The MCP server MUST be implemented in this directory (the MCP app directory that holds this file). Paths below are relative to it.
By default it provides tools for DataRobot operations, but can be extended with custom tools for any domain.

## MCP Server Development Guidelines

IMPORTANT: Do NOT import code from outside of this directory. The MCP server has independent dependencies to avoid conflicts. 
           The MCP server runs as an independent service. Agents connect to it via MCP protocol (HTTP), not direct Python imports.

- You may modify files ONLY inside this directory.
- The MCP server is a standard FastMCP application:
  * Tools live in `app/tools/`
  * Prompts live in `app/prompts/`
  * Resources live in `app/resources/`
  * Configuration is in `app/core/`
  * Tests are in `app/tests/`

## Tool Development Architecture

The MCP server uses auto-discovery for tools:

1. **Tool Definition** (`app/tools/{domain}_tools.py`): Define tools with `@dr_mcp_tool` decorator
2. **Auto-Discovery**: Server automatically loads all tools from `app/tools/` on startup
3. **MCP Protocol**: Agents discover and call tools via HTTP (no imports needed)

**When adding new tools:**
- Create tool functions in `app/tools/{domain}_tools.py`
- Use `@dr_mcp_tool(tags={"category", "action"})` decorator
- Define parameters with `Annotated[type, "description"]`
- Return `ToolResult(structured_content={...})`
- Tools are automatically discovered - no registration needed

**CRITICAL - Tool Implementation Requirements:**

All tool functions MUST be `async def` and return `ToolResult`. Example:

```python
from typing import Annotated
from datarobot_genai.drmcp import dr_mcp_tool
from fastmcp.tools.tool import ToolResult

@dr_mcp_tool(tags={"domain", "action"})
async def tool_name(
    param: Annotated[str, "Parameter description for LLM"],
) -> ToolResult:
    """
    Tool description that the LLM will see.
    Be clear and specific about what the tool does.
    """
    # Your implementation here
    result = {"key": "value"}
    return ToolResult(structured_content=result)
```

## MCP Server Security

- NEVER hardcode API keys or secrets in tool code. Use environment variables or runtime parameters.
- Store credentials in `.env` file (never commit to git)
- Access config via `app/core/user_config.py`
- Use DataRobot credentials management for production deployments

## Installing MCP Server packages

Before making any changes to the MCP server code, install dependencies by running this shell command from this directory:

```shell
task install
```

## MCP Server Testing

Run from this directory:

```shell
task lint
```

```shell
task test
```


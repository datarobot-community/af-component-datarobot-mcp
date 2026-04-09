<p align="center">
  <a href="https://github.com/datarobot-community/af-component-fastmcp-backend">
    <img src="https://af.datarobot.com/img/datarobot_logo.avif" width="600px" alt="DataRobot Logo"/>
  </a>
</p>
<p align="center">
    <span style="font-size: 1.5em; font-weight: bold; display: block;">af-component-fastmcp-backend</span>
</p>

<p align="center">
  <a href="https://datarobot.com">Homepage</a>
  ·
  <a href="https://af.datarobot.com">Documentation</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html">Support</a>
</p>

<p align="center">
  <a href="https://github.com/datarobot-community/af-component-fastmcp-backend/tags">
    <img src="https://img.shields.io/github/v/tag/datarobot-community/af-component-fastmcp-backend?label=version" alt="Latest Release">
  </a>
  <a href="/LICENSE">
    <img src="https://img.shields.io/github/license/datarobot-community/af-component-fastmcp-backend" alt="License">
  </a>
</p>

The FastMCP Component. Deploys a DataRobot MCP server with a variety of baked-in tools

> [!WARNING]
> **This repository is no longer supported.** Please use the public replacement instead: [af-component-datarobot-mcp](https://github.com/datarobot-community/af-component-datarobot-mcp)

`af-component-fastmcp-backend` is a DataRobot App Framework component for teams that need to expose MCP (Model Context Protocol) tools from a DataRobot-hosted backend. It ships a FastMCP server preconfigured with a set of built-in DataRobot tools and wires it into the App Framework deployment lifecycle.

The component packages a FastAPI application built on the [FastMCP](https://gofastmcp.com) library and deploys it as a DataRobot custom application. It is intended for internal teams and app developers building agentic workflows that call DataRobot capabilities via MCP.

# Table of contents

- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Component dependencies](#component-dependencies)
- [Local development](#local-development)
- [Troubleshooting](#troubleshooting)
- [Next steps and cross-links](#next-steps-and-cross-links)
- [Contributing, changelog, support, and legal](#contributing-changelog-support-and-legal)

# Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) installed
- [`dr`](https://cli.datarobot.com) installed

A DataRobot account with permissions to create custom applications is required. The `dr` CLI must be authenticated against your DataRobot environment before running any deployment commands (`dr auth login`).

# Quick start

Run the following command in your project directory:

```bash
dr component add https://github.com/datarobot-community/af-component-fastmcp-backend .
```

Alternatively, you can use `uvx` copier:

```bash
uvx copier copy datarobot-community/af-component-fastmcp-backend .
```

After adding the component:

1. Ensure all required component dependencies have been applied first (see [Component dependencies](#component-dependencies)).
2. Set any required environment variables or configuration values prompted by the copier wizard.
3. Deploy the application using `dr app deploy` or the App Framework deployment task.
4. Confirm the MCP server is reachable by hitting its health endpoint.

# Component dependencies

## Required

The following components must be applied to the project **before** this component:

| Name | Repository | Repeatable |
|------|-----------|------------|
| `base` | [https://github.com/datarobot-community/af-component-fastmcp-backend](https://github.com/datarobot-community/af-component-fastmcp-backend) | No |

# Local development

To run the MCP server locally:

1. Install dependencies: `uv sync`
2. Start the FastMCP server: `uv run fastmcp run <entrypoint>`
3. The server listens on `localhost:8000` by default. Point an MCP client at `http://localhost:8000/mcp` to inspect available tools.

Key directories:

| Path | Purpose |
|------|---------|
| `src/` | FastMCP server entrypoint and tool definitions |
| `infra/` | Pulumi infrastructure configuration |

# Troubleshooting

**Server fails to start**
Verify that all required environment variables (API token, DataRobot endpoint URL) are set. Check that `uv sync` completed without errors.

**Tools not appearing in MCP client**
Confirm the server process is running and the client URL points to the correct endpoint (typically `/mcp` or `/sse`).

**Deployment errors**
Ensure `dr` is authenticated (`dr auth status`) and that your account has custom application creation permissions.

# Next steps and cross-links

- [af-component-datarobot-mcp](https://github.com/datarobot-community/af-component-datarobot-mcp) — the supported replacement for this component
- [App Framework documentation](https://af.datarobot.com) — full App Framework reference
- [FastMCP documentation](https://gofastmcp.com) — FastMCP library reference
- [DataRobot custom applications](https://docs.datarobot.com/en/docs/more-info/apps/custom-apps.html) — deploying custom apps on DataRobot

# Contributing, changelog, support, and legal

This repository is **no longer actively maintained**. For new projects, use [af-component-datarobot-mcp](https://github.com/datarobot-community/af-component-datarobot-mcp).

For historical issues or questions, open a [GitHub Issue](https://github.com/datarobot-community/af-component-fastmcp-backend/issues). For general DataRobot support, visit the [support portal](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html).

This project is licensed under the terms of the [LICENSE](./LICENSE) file included in the repository.

<p align="center">
  <a href="https://github.com/datarobot-community/af-component-datarobot-mcp">
    <img src="docs/img/datarobot_logo.avif" width="600px" alt="DataRobot Logo"/>
  </a>
</p>
<h3 align="center">DataRobot Application Framework</h3>
<h1 align="center">af-component-datarobot-mcp</h1>

<p align="center">
  <a href="https://datarobot.com">Homepage</a>
  ·
  <a href="https://datarobot.atlassian.net/wiki/spaces/BOPS/pages/6542032899/App+Framework+-+Studio">App Framework Documentation</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html">Support</a>
</p>

<p align="center">
  <a href="/LICENSE">
    <img src="https://img.shields.io/github/license/datarobot/af-component-agent" alt="License">
  </a>
</p>

The DataRobot MCP Server One-to-Many component from [App Framework Studio](https://github.com/datarobot/app-framework-studio)

Covers the basic structure and answers needed to have a basic MCP Server
app that is deployable as part of an App Template.


## Getting Started

To use this template, it expects the base component https://github.com/datarobot/af-component-base has already been
installed. To do that first, run:
```bash
uvx copier copy https://github.com/datarobot/af-component-base .
# uvx copier copy git@github.com:datarobot/af-component-base.git .
```

To add the MCP component to your project, you can use the `uvx copier` command to copy the template from this repository:
```bash
uvx copier copy https://github.com/datarobot-community/af-component-datarobot-mcp .
# uvx copier copy git@github.com:datarobot-community/af-component-datarobot-mcp.git .
```

If a template requires multiple MCP backends, it can be used multiple times with a different answer to the `mcp_app_name` question.

To update an existing MCP template, you can use the `uvx copier update` command. This will update the template files:
```bash
uvx copier update -a .datarobot/answers/drmcp-{{ mcp_app_name }}.yml -A
```

To update all templates that are copied:
```bash
uvx copier update -a .datarobot/answers/* -A
```

or just

```bash
uvx copier update -a .datarobot/*
```


## Developer Guide
Please see the [Development Documentation](template/{{mcp_app_name}}/dev.md).


# Get help

If you encounter issues or have questions, try the following:

- Check [the documentation](https://datarobot.atlassian.net/wiki/spaces/BOPS/pages/6542032899/App+Framework+-+Studio) for App Framework Studio.
- [Contact DataRobot](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html) for support.
- Open an issue on the [GitHub repository](https://github.com/datarobot-community/af-component-datarobot-mcp).

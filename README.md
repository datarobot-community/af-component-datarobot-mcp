# af-component-datarobot-mcp

The DataRobot MCP Server One-to-Many component from [App Framework Studio](https://github.com/datarobot/app-framework-studio)

Covers the basic structure and answers needed to have a basic MCP Server
app that is deployable as part of an App Template and can serve a
React Frontend Component:
https://github.com/datarobot/af-component-react


* Part of https://datarobot.atlassian.net/wiki/spaces/BOPS/pages/6542032899/App+Framework+-+Studio


## Instructions

To start for a repo:

`uvx copier copy https://github.com/datarobot-community/af-component-datarobot-mcp .`

If a template requires multiple MCP backends, it can be used multiple times with a different answer to the `mcp_app_name` question.

To work, it expects the base component https://github.com/datarobot/af-component-base has already been installed. To do that first, run:

`uvx copier copy https://github.com/datarobot/af-component-base .`


To update

`uvx copier update -a .datarobot/answers/drmcp-{{ mcp_app_name }}.yml -A`

To update all templates that are copied:

`uvx copier update -a .datarobot/answers/* -A`

or just

`uvx copier update -a .datarobot/*`

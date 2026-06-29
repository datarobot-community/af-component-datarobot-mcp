<p align="center">
  <a href="https://github.com/datarobot-community/af-component-datarobot-mcp">
    <img src="https://af.datarobot.com/img/datarobot_logo.avif" width="600px" alt="DataRobot Logo"/>
  </a>
</p>
<p align="center">
    <span style="font-size: 1.5em; font-weight: bold; display: block;">af-component-datarobot-mcp</span>
</p>

<p align="center">
  <a href="https://datarobot.com">Homepage</a>
  ·
  <a href="https://af.datarobot.com">Documentation</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html">Support</a>
</p>

<p align="center">
  <a href="https://github.com/datarobot-community/af-component-datarobot-mcp/tags">
    <img src="https://img.shields.io/github/v/tag/datarobot-community/af-component-datarobot-mcp?label=version" alt="Latest Release">
  </a>
  <a href="/LICENSE">
    <img src="https://img.shields.io/github/license/datarobot-community/af-component-datarobot-mcp" alt="License">
  </a>
  <a href="https://join.slack.com/t/datarobot-community/shared_invite/zt-3uzfp8k50-SUdMqeux25ok9_5wr4okrg">
    <img src="https://img.shields.io/badge/%23applications-a?label=Slack&labelColor=30373D&color=81FBA6" alt="Slack #applications">
  </a>
</p>

This component is part of the [DataRobot App Framework](https://af.datarobot.com) and deploys a DataRobot MCP (Model Context Protocol) server as a DataRobot custom model application. It is designed for app developers and platform engineers who need to expose DataRobot ML/AI capabilities to LLM-based agents and tools.

The component ships a ready-to-deploy MCP server that includes a comprehensive set of DataRobot predictive tools (project management, model training, deployments, and batch/real-time predictions) as well as integrations for popular collaboration platforms (Google Drive, Jira, Confluence, and Microsoft Graph). It runs as a FastMCP server and can be applied multiple times in the same project under different names to support one-to-many MCP backends in a single template.

# Table of contents

- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Component dependencies](#component-dependencies)
- [Documentation](#documentation)
- [Available tools](#available-tools)
- [Troubleshooting](#troubleshooting)
- [Next steps and cross-links](#next-steps-and-cross-links)
- [Contributing, changelog, support, and legal](#contributing-changelog-support-and-legal)

# Prerequisites

The following tools must be installed before using this component.

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) installed
- [`dr`](https://cli.datarobot.com) installed
- An active DataRobot account with [API credentials](https://docs.datarobot.com/en/docs/platform/acct-settings/api-key-mgmt.html#api-keys-and-tools)

The `base` component must be applied to the project before this component. See [Component dependencies](#component-dependencies) for details.

# Quick start

Run the following command in your project directory:

```bash
dr component add https://github.com/datarobot-community/af-component-datarobot-mcp .
```

If you need additional control, you can run this to use copier directly:

```bash
uvx copier copy datarobot-community/af-component-datarobot-mcp .
```

During setup you will be prompted for an `mcp_app_name`. This name scopes all generated files and answers for this MCP backend, which lets you apply the component multiple times in the same project for different server instances.

# Component dependencies

## Required

The following components must be applied to the project **before** this component:

| Name | Repository | Repeatable |
|------|-----------|------------|
| `base` | [https://github.com/datarobot-community/af-component-base](https://github.com/datarobot-community/af-component-base) | No |

## Local development

After applying the component, the following paths contain the key files for development.

| Path | Purpose |
|------|---------|
| `template/{{mcp_app_name_file}}/` | Generated MCP server source (tools, server entrypoint). |
| `template/docs/datarobot-mcp/` | MCP server documentation (rendered to `docs/datarobot-mcp/` in the target project). |
| `.datarobot/answers/drmcp-{{ mcp_app_name }}.yml` | Copier answers file for this instance. |


To run the MCP server locally:

```bash
uv run python -m MCP_APP_NAME
```

Refer to the [MCP server documentation](template/docs/datarobot-mcp/README.md) for the full developer guide, including OAuth provider configuration for integration tools.

# Documentation

After applying this component, MCP guides are available under `docs/datarobot-mcp/` in your project. In this repository, the template sources live under [`template/docs/datarobot-mcp/`](template/docs/datarobot-mcp/README.md):

| Document | Description |
|---|---|
| [Overview](template/docs/datarobot-mcp/README.md) | Getting started, local dev, and deployment overview |
| [MCP client setup](template/docs/datarobot-mcp/mcp_client_setup.md) | Configure Cursor, VS Code, and Claude Desktop |
| [Server architecture](template/docs/datarobot-mcp/mcp_server_architecture.md.jinja) | Project structure and configuration reference |
| [Dynamic tool registration](template/docs/datarobot-mcp/dynamic_tool_registration.md) | Turn DataRobot deployments into tools automatically |
| [Custom tools](template/docs/datarobot-mcp/custom_tools.md.jinja) | Author domain-specific tools |
| [Deployment info tools](template/docs/datarobot-mcp/deployment_info_tools.md) | Query deployment features and build prediction datasets |

## Updating

All components should be regularly updated to pick up bug fixes, new features,
and compatibility with the latest DataRobot App Framework.

For automatic updates to the latest version, run the following command in your project directory:
```bash
dr component update .datarobot/answers/drmcp-<mcp_app_name>.yml
```

If you need more fine grained control and prefer using copier directly,
you can run this to have more control over the process:

```bash
uvx copier update -a .datarobot/answers/drmcp-<mcp_app_name>.yml -A
```

# Available tools

The MCP server provides tools organized into DataRobot platform tools and third-party integration tools (data connectors and web search).

## Data Connectors — Confluence

- **`confluence_get_page`**&mdash;Retrieve Confluence page contents by ID or by exact title within a space.
- **`confluence_create_page`**&mdash;Create a new Confluence page in a space, optionally under a parent page.
- **`confluence_add_comment`**&mdash;Add a comment to an existing Confluence page.
- **`confluence_search_space`**&mdash;Search Confluence content using Confluence Query Language (CQL).
- **`confluence_update_page`**&mdash;Update the body of an existing Confluence page (requires current page version number).

## Data Connectors — Jira

- **`jira_search_issues`**&mdash;Find Jira issues matching a JQL query.
- **`jira_get_issue`**&mdash;Get full details for a single Jira issue (requires issue key, e.g., PROJ-123).
- **`jira_create_issue`**&mdash;Create a new Jira issue in a project.
- **`jira_update_issue`**&mdash;Update fields on an existing Jira issue.
- **`jira_transition_issue`**&mdash;Move a Jira issue to a new workflow status.

## Data Connectors — Google Drive

- **`gdrive_find_contents`**&mdash;Search Google Drive for files and folders, using optional query and pagination parameters.
- **`gdrive_read_and_export_content`**&mdash;Read and export the text content of a Google Drive file.
- **`gdrive_create_file`**&mdash;Create a new file or folder in Google Drive.
- **`gdrive_update_metadata`**&mdash;Rename, star, or delete a Google Drive file.
- **`gdrive_manage_access`**&mdash;Add, update, or remove sharing permissions on a Google Drive file.

## Data Connectors — Microsoft 365

- **`microsoft_graph_search_content`**&mdash;Search SharePoint and OneDrive for files and list items.
- **`microsoft_graph_share_item`**&mdash;Share a SharePoint or OneDrive file or folder.
- **`microsoft_graph_create_file`**&mdash;Create a new plain-text file in OneDrive or SharePoint.
- **`microsoft_graph_update_metadata`**&mdash;Update name or metadata on a SharePoint list item or drive item.

## Web Search — Perplexity

- **`perplexity_search`**&mdash;Search the public web and return ranked sources and snippets for a question.
- **`perplexity_sonar`**&mdash;Get a cited AI-generated answer or research report from Perplexity; available model options are `sonar`, `sonar-reasoning-pro`, and `sonar-deep-research`.

## Web Search — Tavily

- **`tavily_search_web`**&mdash;Search the public web by keyword and return ranked results.
- **`tavily_extract_text`**&mdash;Extract clean text from one or more web page URLs.
- **`tavily_list_links`**&mdash;List links discovered under a website URL.
- **`tavily_crawl_site`**&mdash;Crawl a website to collect multiple related pages.

## DataRobot Documentation

- **`datarobot_docs_fetch_page`**&mdash;Retrieve the full text of a DataRobot documentation page by URL.

## DataRobot — Use Cases

- **`datarobot_usecases_list`**&mdash;List DataRobot Use Cases with optional name filter.
- **`usecases_list_assets`**&mdash;List datasets, deployments, and experiments linked to use cases.

## DataRobot — Catalog (Datasets & Datastores)

- **`catalog_upload_dataset`**&mdash;Upload or register a dataset from a local file or URL.
- **`catalog_list_datasets`**&mdash;List datasets registered in DataRobot.
- **`catalog_get_preview`**&mdash;Get metadata and optional sample rows for a dataset.
- **`catalog_list_datastores`**&mdash;List external database and storage connections configured in DataRobot.
- **`catalog_browse_datastore`**&mdash;Browse schemas, tables, or folders inside an external datastore.
- **`catalog_query_datastore`**&mdash;Run SQL against an external datastore.
- **`catalog_check_timeseries_eligibility`**&mdash;Check whether a dataset is ready for time series modeling.
- **`catalog_analyze_dataset`**&mdash;Return profile of an AI Catalog dataset (columns, types, and missing values).
- **`catalog_suggest_ml_problems`**&mdash;Recommend a target, which defines a problem type, from a dataset.
- **`catalog_get_eda_insights`**&mdash;Run exploratory data analysis (EDA) on a dataset and return summary statistics.

## DataRobot — Modeling (Projects & Models)

- **`models_get_bestmodel`**&mdash;Get the top-performing model on a model leaderboard.
- **`modeling_score_dataset`**&mdash;Score a catalog dataset with a trained model from a project leaderboard (async job).
- **`modeling_list_models`**&mdash;List all leaderboard models.
- **`modeling_get_modeldetails`**&mdash;Get training metrics and diagnostics for a leaderboard model.
- **`modeling_list_projects`**&mdash;List all modeling projects associated with the user's organization.
- **`modeling_get_project_dataset`**&mdash;Find a project dataset (requires project name).
- **`modeling_start_autopilot`**&mdash;Start or resume Autopilot training for a modeling project.
- **`modeling_get_model_roc`**&mdash;Get ROC curve data&mdash;classification, performance, and statistics&mdash;for a binary classification model.
- **`modeling_get_model_feature_impact`**&mdash;Get model feature impact, which identifies the features most strongly driving model decisions.
- **`modeling_get_model_lift_chart`**&mdash;Get lift chart data for a binary or multiclass classification model.

## DataRobot — Deployments

- **`deployment_get_list`**&mdash;List MLOps deployments in DataRobot.
- **`deployment_get_model_info`**&mdash;Get the model record linked to a deployment (requires deployment ID).
- **`deployment_create_deployment`**&mdash;Create a new deployment from a trained leaderboard model.
- **`deployment_get_prediction_history`**&mdash;Retrieve logged prediction history for a deployment.
- **`deployment_get_info`**&mdash;Get deployment scoring information: feature details, model settings, and deployment ID.
- **`deployment_generate_prediction_sample`**&mdash;Generate sample prediction rows with required columns for valid prediction output.
- **`deployment_validate_prediction_data`**&mdash;Validate inline CSV prediction data against a deployment schema.
- **`deployment_get_features`**&mdash;Get input features, including target summary, for a deployment.

## DataRobot — Predictions

- **`predict_batch_predictions_from_dataset`**&mdash;Generate batch predictions from a deployment using a supplied dataset.
- **`predict_batch_predictions_from_holdout_data`**&mdash;Generate batch predictions from a deployment using the holdout partition data.
- **`predict_get_batch_job_status`**&mdash;Check status of a batch prediction job.
- **`predict_get_batch_results`**&mdash;Download scored results from a completed batch prediction job.
- **`predict_score_catalog_realtime`**&mdash;Score a catalog dataset through a deployment and return rows immediately.
- **`predict_score_inline_realtime`**&mdash;Score inline CSV or JSON rows through a deployment immediately.

## DataRobot — Vector Databases (VDB)

- **`vdb_list`**&mdash;List deployed vector database (VDB) deployments.
- **`vdb_query`**&mdash;Run semantic search against a vector database deployment.

Integration tools (Google Drive, Jira, Confluence, Microsoft 365) require OAuth authentication configured via DataRobot OAuth providers. Perplexity and Tavily tools require API keys. See [MCP client setup](template/docs/datarobot-mcp/mcp_client_setup.md) and [server architecture](template/docs/datarobot-mcp/mcp_server_architecture.md.jinja) for configuration details.

# Troubleshooting

Common issues and their solutions are listed below.

**`dr` command not found** — Ensure the DataRobot CLI is installed and on your `PATH`. See the [CLI docs](https://cli.datarobot.com) for install instructions.

**Copier prompts fail or produce unexpected output** — Confirm you are running `uv` 0.4+ and that `copier` resolves via `uvx`. Run `uvx copier --version` to verify.

**Integration tools return auth errors** — OAuth providers must be configured in DataRobot before integration tools (Google Drive, Jira, Confluence, Microsoft Graph) will work. See [MCP client setup](template/docs/datarobot-mcp/mcp_client_setup.md).

**Multiple instances conflict** — Each instance must use a unique `mcp_app_name`. If two instances share a name, their answers files and generated directories will collide.

For additional help, [open an issue](https://github.com/datarobot-community/af-component-datarobot-mcp/issues) on the GitHub repository or [contact DataRobot support](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html).

# Next steps and cross-links

Explore the following resources to learn more or extend this component.

- [App Framework documentation](https://af.datarobot.com)&mdash;full platform docs, component catalog, and deployment guides.
- [DataRobot API docs](https://docs.datarobot.com)&mdash;reference for the DataRobot platform APIs used by the predictive tools.
- [FastMCP documentation](https://github.com/jlowin/fastmcp)&mdash;the MCP server framework underlying this component.
- [af-component-base](https://github.com/datarobot-community/af-component-base)&mdash;required base component.
- [MCP server documentation](template/docs/datarobot-mcp/README.md)&mdash;local dev guide, client setup, OAuth configuration, and advanced topics.

# Contributing, changelog, support, and legal

**Contributing** — Fork the repository, make changes on a feature branch, ensure `task lint` passes, and open a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) if present.

**Changelog** — See [CHANGELOG.md](CHANGELOG.md) for version history. This component follows semantic versioning; the current version badge at the top of this README reflects the latest release tag.

**Getting help** — Open an issue on the [GitHub repository](https://github.com/datarobot-community/af-component-datarobot-mcp/issues) or reach out via [DataRobot support](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html).

**License** — This project is licensed under the terms shown in the [LICENSE](LICENSE) file.

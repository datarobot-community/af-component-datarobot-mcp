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
</p>

The FastMCP Component. Deploys a DataRobot MCP server with a variety of baked-in tools

This component is part of the [DataRobot App Framework](https://af.datarobot.com) and deploys a DataRobot MCP (Model Context Protocol) server as a DataRobot custom model application. It is designed for app developers and platform engineers who need to expose DataRobot ML/AI capabilities to LLM-based agents and tools.

The component ships a ready-to-deploy MCP server that includes a comprehensive set of DataRobot predictive tools (project management, model training, deployments, and batch/real-time predictions) as well as integrations for popular collaboration platforms (Google Drive, Jira, Confluence, and Microsoft Graph). It runs as a FastMCP server and can be applied multiple times in the same project under different names to support one-to-many MCP backends in a single template.


# Table of contents

- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Component dependencies](#component-dependencies)
- [Available tools](#available-tools)
- [Local development](#local-development)
- [Troubleshooting](#troubleshooting)
- [Next steps and cross-links](#next-steps-and-cross-links)
- [Contributing, changelog, support, and legal](#contributing-changelog-support-and-legal)

# Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) installed
- [`dr`](https://cli.datarobot.com) installed
- An active DataRobot account with [API credentials](https://docs.datarobot.com/en/docs/platform/acct-settings/api-key-mgmt.html#api-keys-and-tools)

The `base` component must be applied to the project before this component. See [Component dependencies](#component-dependencies) for details.

# Quick start

Run the following command in your project directory:

```bash
dr component add https://github.com/datarobot-community/af-component-datarobot-mcp .
```

Alternatively, you can use `uvx` copier:

```bash
uvx copier copy datarobot-community/af-component-datarobot-mcp .
```

During setup you will be prompted for an `mcp_app_name`. This name scopes all generated files and answers for this MCP backend, which lets you apply the component multiple times in the same project for different server instances.

**Update an existing instance**

```bash
uvx copier update -a .datarobot/answers/drmcp-{{ mcp_app_name }}.yml -A
```

**Update all component instances**

```bash
uvx copier update -a .datarobot/answers/drmcp-*.yml -A
```


# Component dependencies

## Required

The following components must be applied to the project **before** this component:

| Name | Repository | Repeatable |
|------|-----------|------------|
| `base` | [https://github.com/datarobot-community/af-component-datarobot-mcp](https://github.com/datarobot-community/af-component-datarobot-mcp) | No |

# Available tools

The MCP server provides tools organized into two categories: DataRobot predictive tools and third-party integration tools.

## Predictive tools (DataRobot ML/AI)

### Data management

- **`upload_dataset_to_ai_catalog`** — Upload a dataset to the DataRobot AI Catalog/Data Registry from a local file or URL
- **`list_ai_catalog_items`** — List all AI Catalog items (datasets) for the authenticated user

### Deployment information

- **`get_deployment_info`** — Retrieve deployment information, including required features and model metadata
- **`generate_prediction_data_template`** — Generate a CSV template with the correct structure for making predictions
- **`validate_prediction_data`** — Validate if a CSV file is suitable for making predictions with a deployment
- **`get_deployment_features`** — Retrieve only the features list for a deployment as JSON

### Deployment management

- **`list_deployments`** — List all DataRobot deployments for the authenticated user
- **`get_model_info_from_deployment`** — Get model info associated with a given deployment ID
- **`deploy_model`** — Deploy a model by creating a new DataRobot deployment

### Model management

- **`get_best_model`** — Get the best model for a DataRobot project, optionally by a specific metric
- **`score_dataset_with_model`** — Score a dataset using a specific DataRobot model
- **`list_models`** — List all models in a project

### Predictions

- **`predict_by_file_path`** — Make batch predictions using a DataRobot deployment and a local CSV file (for large datasets)
- **`predict_by_ai_catalog`** — Make batch predictions using a DataRobot deployment and an AI Catalog dataset
- **`predict_from_project_data`** — Make predictions using training data associated with a project (holdout, validation, or all backtest partitions)
- **`predict_realtime`** — Make real-time predictions using a deployment and a local CSV file or dataset string (supports time series, explanations, and custom thresholds)
- **`predict_by_ai_catalog_rt`** — Make real-time predictions using a deployment and an AI Catalog dataset

### Project management

- **`list_projects`** — List all DataRobot projects for the authenticated user
- **`get_project_dataset_by_name`** — Get a dataset ID by name for a given project

### Training & analysis

- **`analyze_dataset`** — Analyze a dataset to understand its structure and potential use cases
- **`suggest_use_cases`** — Analyze a dataset and suggest potential machine learning use cases
- **`get_exploratory_insights`** — Generate exploratory data insights for a dataset
- **`start_autopilot`** — Start automated model training (Autopilot) for a project
- **`get_model_roc_curve`** — Get detailed ROC curve for a specific model
- **`get_model_feature_impact`** — Get detailed feature impact for a specific model
- **`get_model_lift_chart`** — Get detailed lift chart for a specific model

## Integration tools

Integration tools require OAuth authentication configured via DataRobot OAuth providers. See the [Development Documentation](template/{{mcp_app_name_file}}/dev.md) for configuration details.

### Google Drive

- **`gdrive_find_contents`** — Search or list files in Google Drive with pagination and filtering (currently disabled)
- **`gdrive_read_content`** — Retrieve the content of a specific file by its ID (auto-converts Google Workspace files to readable formats)
- **`gdrive_create_file`** — Create a new file or folder in Google Drive (currently disabled)
- **`gdrive_update_metadata`** — Update non-content metadata fields (rename, star, trash) (currently disabled)
- **`gdrive_manage_access`** — Manage file/folder sharing and permissions (add, update, remove access)

### Jira

- **`jira_search_issues`** — Search for Jira issues using JQL (Jira Query Language)
- **`jira_get_issue`** — Retrieve all fields and details for a single Jira issue by its key
- **`jira_create_issue`** — Create a new Jira issue with mandatory project, summary, and type information
- **`jira_update_issue`** — Modify descriptive fields or custom fields on an existing Jira issue
- **`jira_transition_issue`** — Move a Jira issue through its workflow to a new status

### Confluence

- **`confluence_get_page`** — Retrieve the content of a specific Confluence page by ID or title
- **`confluence_create_page`** — Create a new documentation page in a specified Confluence space
- **`confluence_add_comment`** — Add a new comment to a specified Confluence page
- **`confluence_search`** — Search Confluence pages and content using CQL (Confluence Query Language)
- **`confluence_update_page`** — Update the content of an existing Confluence page

### Microsoft Graph

- **`microsoft_graph_search_content`** — Search for SharePoint and OneDrive content using Microsoft Graph Search API with pagination, filtering, and entity type selection

# Local development

Key paths after applying the component:

| Path | Purpose |
|------|---------|
| `template/{{mcp_app_name_file}}/` | Generated MCP server source (tools, server entrypoint) |
| `.datarobot/answers/drmcp-{{ mcp_app_name }}.yml` | Copier answers file for this instance |

To run the MCP server locally:

```bash
uv run python -m <mcp_app_name>
```

Refer to the [Development Documentation](template/{{mcp_app_name_file}}/dev.md) for the full developer guide, including OAuth provider configuration for integration tools.

# Troubleshooting

**`dr` command not found** — Ensure the DataRobot CLI is installed and on your `PATH`. See the [CLI docs](https://cli.datarobot.com) for install instructions.

**Copier prompts fail or produce unexpected output** — Confirm you are running `uv` 0.4+ and that `copier` resolves via `uvx`. Run `uvx copier --version` to verify.

**Integration tools return auth errors** — OAuth providers must be configured in DataRobot before integration tools (Google Drive, Jira, Confluence, Microsoft Graph) will work. See the dev.md guide inside the generated template directory.

**Multiple instances conflict** — Each instance must use a unique `mcp_app_name`. If two instances share a name, their answers files and generated directories will collide.

For additional help, [open an issue](https://github.com/datarobot-community/af-component-datarobot-mcp/issues) on the GitHub repository or [contact DataRobot support](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html).

# Next steps and cross-links

- [App Framework documentation](https://af.datarobot.com) — full platform docs, component catalog, and deployment guides
- [DataRobot API docs](https://docs.datarobot.com) — reference for the DataRobot platform APIs used by the predictive tools
- [FastMCP documentation](https://github.com/jlowin/fastmcp) — the MCP server framework underlying this component
- [af-component-base](https://github.com/datarobot-community/af-component-base) — required base component
- [Development Documentation](template/{{mcp_app_name_file}}/dev.md) — local dev guide, OAuth setup, and advanced configuration

# Contributing, changelog, support, and legal

**Contributing** — Fork the repository, make changes on a feature branch, ensure `task lint` passes, and open a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) if present.

**Changelog** — See [CHANGELOG.md](CHANGELOG.md) for version history. This component follows semantic versioning; the current version badge at the top of this README reflects the latest release tag.

**Getting help** — Open an issue on the [GitHub repository](https://github.com/datarobot-community/af-component-datarobot-mcp/issues) or reach out via [DataRobot support](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html).

**License** — This project is licensed under the terms shown in the [LICENSE](LICENSE) file.

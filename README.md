<p align="center">
  <a href="https://github.com/datarobot-community/af-component-datarobot-mcp">
    <img src="docs/img/datarobot_logo.avif" width="600px" alt="DataRobot Logo"/>
  </a>
</p>
<h3 align="center">DataRobot application framework</h3>
<h1 align="center">af-component-datarobot-mcp</h1>

<p align="center">
  <a href="https://datarobot.com">Homepage</a>
  ·
  <a href="https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html">Support</a>
</p>

<p align="center">
  <a href="/LICENSE">
    <img src="https://img.shields.io/github/license/datarobot/af-component-agent" alt="License">
  </a>
</p>

The DataRobot MCP Server One-to-Many component from [App Framework Studio](https://github.com/datarobot/app-framework-studio) can be used to create custom user tools and is deployable as a DataRobot custom model application. The server includes a comprehensive set of DataRobot predictive tools out of the box, along with integrations for popular collaboration platforms.

This guide covers the basic structure and answers needed to have a basic MCP Server app that is deployable as part of an App Template.

## Prerequisites

Before you begin, ensure you have the following:

- **uv**: Python package installer and project manager
- **DataRobot Account**: Active DataRobot account with [API credentials](https://docs.datarobot.com/en/docs/platform/acct-settings/api-key-mgmt.html#api-keys-and-tools)
- **Python 3.11+**: Required Python version

## Getting started

This template requires the [base component](https://github.com/datarobot/af-component-base) to be installed.
Use the following command to install the base component:

```bash
uvx copier copy git@github.com:datarobot/af-component-base.git .
```

To add the MCP component to your project, use the following command to copy the template from this repository:

```bash
uvx copier copy git@github.com:datarobot-community/af-component-datarobot-mcp.git .
```

If a template requires multiple MCP backends, it can be used multiple times with a different answer to the `mcp_app_name` question.
To update an existing MCP template in the project, use the following command to update the template files:

```bash
uvx copier update -a .datarobot/answers/drmcp-{{ mcp_app_name }}.yml -A
```

To update all templates in the project, use the following command:

```bash
uvx copier update -a .datarobot/answers/* -A
```

To update all files in the project, use the following command:

```bash
uvx copier update -a .datarobot/*
```

## Available tools

The MCP server provides a wide range of tools organized into the following categories:

### Predictive tools (DataRobot ML/AI)

The MCP server provides a variety of tools for managing and working with DataRobot ML/AI models and deployments.
See the sections below for more details on each tool.

#### Data management

- **`upload_dataset_to_ai_catalog`** — Upload a dataset to the DataRobot AI Catalog/Data Registry from a local file or URL
- **`list_ai_catalog_items`** — List all AI Catalog items (datasets) for the authenticated user

#### Deployment information

- **`get_deployment_info`** — Retrieve deployment information, including required features and model metadata
- **`generate_prediction_data_template`** — Generate a CSV template with the correct structure for making predictions
- **`validate_prediction_data`** — Validate if a CSV file is suitable for making predictions with a deployment
- **`get_deployment_features`** — Retrieve only the features list for a deployment as JSON

#### Deployment management

- **`list_deployments`** — List all DataRobot deployments for the authenticated user
- **`get_model_info_from_deployment`** — Get model info associated with a given deployment ID
- **`deploy_model`** — Deploy a model by creating a new DataRobot deployment

#### Model management

- **`get_best_model`** — Get the best model for a DataRobot project, optionally by a specific metric
- **`score_dataset_with_model`** — Score a dataset using a specific DataRobot model
- **`list_models`** — List all models in a project

#### Predictions

- **`predict_by_file_path`** — Make batch predictions using a DataRobot deployment and a local CSV file (for large datasets)
- **`predict_by_ai_catalog`** — Make batch predictions using a DataRobot deployment and an AI Catalog dataset
- **`predict_from_project_data`** — Make predictions using training data associated with a project (holdout, validation, or all backtest partitions)
- **`predict_realtime`** — Make real-time predictions using a deployment and a local CSV file or dataset string (supports time series, explanations, and custom thresholds)
- **`predict_by_ai_catalog_rt`** — Make real-time predictions using a deployment and an AI Catalog dataset

#### Project management

- **`list_projects`** — List all DataRobot projects for the authenticated user
- **`get_project_dataset_by_name`** — Get a dataset ID by name for a given project

#### Training & analysis

- **`analyze_dataset`** — Analyze a dataset to understand its structure and potential use cases
- **`suggest_use_cases`** — Analyze a dataset and suggest potential machine learning use cases
- **`get_exploratory_insights`** — Generate exploratory data insights for a dataset
- **`start_autopilot`** — Start automated model training (Autopilot) for a project
- **`get_model_roc_curve`** — Get detailed ROC curve for a specific model
- **`get_model_feature_impact`** — Get detailed feature impact for a specific model
- **`get_model_lift_chart`** — Get detailed lift chart for a specific model

### Integration tools

The following integration tools require authentication to be configured via DataRobot OAuth providers:

#### Google Drive tools

- **`gdrive_find_contents`** — Search or list files in Google Drive with pagination and filtering (currently disabled)
- **`gdrive_read_content`** — Retrieve the content of a specific file by its ID (auto-converts Google Workspace files to readable formats)
- **`gdrive_create_file`** — Create a new file or folder in Google Drive (currently disabled)
- **`gdrive_update_metadata`** — Update non-content metadata fields (rename, star, trash) (currently disabled)
- **`gdrive_manage_access`** — Manage file/folder sharing and permissions (add, update, remove access)

#### Jira tools

- **`jira_search_issues`** — Search for Jira issues using JQL (Jira Query Language)
- **`jira_get_issue`** — Retrieve all fields and details for a single Jira issue by its key
- **`jira_create_issue`** — Create a new Jira issue with mandatory project, summary, and type information
- **`jira_update_issue`** — Modify descriptive fields or custom fields on an existing Jira issue
- **`jira_transition_issue`** — Move a Jira issue through its workflow to a new status

#### Confluence tools

- **`confluence_get_page`** — Retrieve the content of a specific Confluence page by ID or title
- **`confluence_create_page`** — Create a new documentation page in a specified Confluence space
- **`confluence_add_comment`** — Add a new comment to a specified Confluence page
- **`confluence_search`** — Search Confluence pages and content using CQL (Confluence Query Language)
- **`confluence_update_page`** — Update the content of an existing Confluence page

#### Microsoft Graph tools

- **`microsoft_graph_search_content`** — Search for SharePoint and OneDrive content using Microsoft Graph Search API with pagination, filtering, and entity type selection

>[NOTE] Integration tools require OAuth authentication to be configured via DataRobot OAuth providers. See the [Development Documentation](template/{{mcp_app_name}}/dev.md) for configuration details.

## Developer guide

Refer to the [Development Documentation](template/{{mcp_app_name}}/dev.md) for more details on the developer guide.

# Get help

If you encounter issues or have questions, try the following:

- [Contact DataRobot](https://docs.datarobot.com/en/docs/get-started/troubleshooting/general-help.html) for support.
- Open an issue on the [GitHub repository](https://github.com/datarobot-community/af-component-datarobot-mcp).

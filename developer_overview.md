## Developer Overview

### What this repo is
A template-backed FastMCP backend component that exposes DataRobot capabilities as MCP “tools” (and a couple of HTTP routes) for use by LLM clients and UIs. It includes opinionated infrastructure around config, credentials, logging with secret redaction, OpenTelemetry tracing, tool tagging/discovery, and large-result handling via S3. It’s meant to be copied into an App Framework project and extended with product-specific “recipe” tools.

### Runtime model
- **Boot flow**: The process boots a FastMCP server, dynamically imports modules under `app/base` and `app/recipe`, and registers all decorated tools/prompts/resources.
- **Invocation**: Clients call tools through MCP (HTTP transport enabled), or hit lightweight REST endpoints for health and tag discovery.
- **Cross-cutting concerns**: Every tool runs with standardized logging/redaction and optional OTEL spans (plus optional HTTP client instrumentation). DataRobot SDK clients use the caller’s Bearer token if present, else service credentials from `.env`.
- **Large outputs**: Tool outputs are returned inline unless large; large tabular results are uploaded to S3 and exposed as presigned URLs and MCP resources.

### Key entry points and flow
- **Server entry**: `app/main.py` creates and runs a `DataRobotMCPServer` with the global `mcp` instance.
- **Server wiring**: `app/base/core/dr_mcp_server.py.jinja` composes config/credentials/logging/telemetry; dynamically imports `tools`, `prompts`, `resources`; exposes `GET /` health and `GET /tags` routes; starts FastMCP with `streamable-http` transport by default.
- **MCP instance**: `app/base/core/mcp_instance.py` defines `TaggedFastMCP` with tagging support and the global `mcp`. It also provides decorators:
  - `@dr_mcp_tool(tags=[...])` → registers a tool with tags, logging and tracing
  - `@dr_mcp_extras(type="prompt"|"resource"|"tool")` → logging + tracing without registering as a tool

### Directory layout (where things go)
- `app/base/core/` (framework and cross-cutting infra)
  - `config.py`: typed server config via Pydantic Settings; env aliasing supports DataRobot runtime prefixes
  - `credentials.py`: DR API + optional AWS creds; helpers like `has_aws_credentials`
  - `mcp_instance.py`: global `mcp`, tool/prompt decorators, tag support
  - `dr_mcp_server.py.jinja`: server wiring, dynamic discovery of tools/prompts/resources, health and `/tags`
  - `logging.py`: global logging setup with secret redaction and `@log_execution`
  - `telemetry.py`: OTEL initialization, optional HTTP client instrumentation, `@trace_execution`
  - `common.py`: `get_sdk_client` (per-request Bearer token or service creds), S3 bucket info, `MCPError`
  - `constants.py`: defaults like `DEFAULT_DATAROBOT_ENDPOINT`, `MAX_INLINE_SIZE`, env prefix
  - `utils.py`: presigned S3 URL, inline-vs-S3 result helpers, MCP resource registration
- `app/base/tools/` (shared functional tools)
  - Deployments, projects, models, data, training, batch/rt predictions, and MCP metadata (tag discovery)
- `app/base/prompts/` (shared prompts)
  - Example: deployment info prompt
- `app/recipe/*` (your app-specific extensions)
  - `tools/`, `prompts/`, `resources/` auto-register on boot; put product-specific logic here
- `app/base/tests/` and `app/recipe/tests/` (unit, integration, ETE)
- `Taskfile.yaml` for common dev flows (`install`, `dev`, `lint`, `unit/integration/ete`)

### Included capabilities (what’s already built)
- **Discovery and metadata**: `get_all_available_tags`, `list_tools_by_tags`, `get_tool_info_by_name`
- **Projects and models**: `list_projects`, `list_models`, `get_best_model(metric?)`, `get_model_feature_impact`, `get_model_roc_curve`, `get_model_lift_chart`
- **Deployments**: `list_deployments`, `deploy_model`, `get_model_info_from_deployment`
  - Deployment metadata and data requirements: `get_deployment_info`, `get_deployment_features`, `generate_prediction_data_template`, `validate_prediction_data`
- **Datasets**: `upload_dataset_to_ai_catalog`, `list_ai_catalog_items`, `get_project_dataset_by_name`
- **Predictions**
  - Batch via SDK: `predict_with_deployment_by_file_path`, `predict_with_deployment_by_ai_catalog`, `predict_with_deployment_from_project_data`
  - Realtime via datarobot-predict: `predict_realtime` (time series, SHAP/XEMP, passthrough columns) and `predict_with_deployment_by_ai_catalog_rt`
  - Large results saved to S3 with presigned URLs and MCP resources; small results returned inline
- **Training**: `analyze_dataset`, `suggest_use_cases`, `get_exploratory_insights`, `start_autopilot`

### Configuration and credentials (how and why)
- **Pydantic Settings with environment aliasing**
  - Override via `.env` or DataRobot runtime `MLOPS_RUNTIME_PARAM_...` prefix
- **DataRobot SDK client selection**
  - If request has `Authorization: Bearer <token>`, act as that user; else use service token from env
- **OpenTelemetry**
  - Collector defaults to DR endpoint `/otel`; exports spans with `X-DataRobot-Api-Key` and `X-DataRobot-Entity-Id`; optional HTTP client instrumentation

### Logging, errors, and security
- Centralized logging with secret redaction (tokens, AWS keys, etc.)
- `@log_execution` wraps tools for consistent start/finish logging and error capture; rethrows as `MCPError`

### HTTP endpoints (minimal REST)
- `GET /` health
- `GET /tags` returns all tool tags
- Add more RESTful endpoints via `@mcp.custom_route(path, methods=[...])` when needed; prefer MCP tools for most operations

### Why these choices
- **MCP-first**: typed schemas for LLM/editor clients; simpler than bespoke REST everywhere
- **Stateless HTTP transport**: easy local dev and deployment; editor/client friendly
- **Dynamic module discovery**: no manual registration; drop-in tools/prompts/resources
- **Tagging**: discoverability and grouping in UIs and prompt strategies
- **Per-request token**: least-privilege behavior when possible; service auth fallback
- **OTEL**: operational visibility across SDK calls and custom logic
- **S3 resources**: practical large-output handling
- **Strict typing and linters**: maintain quality for contributions

### How to extend (patterns for seniors)
- **Add a tool**
  - Create module under `app/recipe/tools/` (preferred) or `app/base/tools/` (shared)
  - Define an async function, decorate with `@dr_mcp_tool(tags=[...])`
  - For prompts/resources only, use `@dr_mcp_extras(type="prompt"|"resource")`
  - For large dataframes, use `predictions_result_response` or `save_df_to_s3_and_register_resource`
- **Add a REST endpoint**
  - Use `@mcp.custom_route("/v1/thing", methods=["GET"])` and return a `JSONResponse`
- **Use DR SDK with user context**
  - Accept `ctx: Context` and call `get_sdk_client(ctx)` to pick up user Bearer tokens
- **Observability**
  - Set `OTEL_ATTRIBUTES` (JSON) and toggle `OTEL_ENABLED_HTTP_INSTRUMENTORS`; spans capture params and success flags

### Running and testing
- **Run locally**: `uv run app/main.py` or `task dev`; MCP clients can point to `http://localhost:8080/mcp/`
- **Lint and type-check**: `task lint` (ruff + mypy strict)
- **Tests**: `task unit`, `task integration`, `task ete` (ETE spins server on 8082)

### Quick checklist for new devs
- Install uv and run `task install`
- Copy `.env.sample` → `.env`, set `DATAROBOT_API_TOKEN`, `DATAROBOT_ENDPOINT`; add AWS creds if using S3 flows
- `task dev` and point MCP client to `http://localhost:8080/mcp/`
- Hit `GET /` and `GET /tags` to verify
- Browse `app/base/tools/` for patterns; add app-specific tools under `app/recipe/tools/`
- Keep returns small or use S3-backed resources; tag your tools; rely on decorators for logs/traces

### Decisions to preserve
- Use `@dr_mcp_tool` and tags consistently
- Avoid logging sensitive values; keep large results off the wire
- Keep REST endpoints minimal and RESTful; prefer MCP tools
- Use per-request tokens to preserve least-privilege model

### Constraints and caveats
- AWS creds required for S3 upload flows; otherwise S3-dependent tools will error
- Time series realtime predictions require appropriate columns/history
- MCP clients differ in header forwarding; `get_sdk_client` attempts multiple header shapes

### Common environment variables
- **Core**: `DATAROBOT_API_TOKEN`, `DATAROBOT_ENDPOINT`, `MCP_SERVER_PORT`, `APP_LOG_LEVEL`
- **S3**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_PREDICTIONS_S3_BUCKET`, `AWS_PREDICTIONS_S3_PREFIX`
- **OTEL**: `OTEL_COLLECTOR_BASE_URL`, `OTEL_ENTITY_ID`, `OTEL_ATTRIBUTES`, `OTEL_ENABLED_HTTP_INSTRUMENTORS`

### Typical first PR
- Add 1–2 new `app/recipe/tools/*` tools, tag them, add a small E2E test in `app/recipe/tests/ete`, and wire any minimal REST endpoints your UI needs.

### Quality gates and style
- Ruff formatting and linting; mypy strict with Pydantic v2 plugin; imports at top; minimize unrelated edits.

### Template usage
- This repository is a Copier template. See top-level `README.md` for applying alongside `af-component-base`, and for update commands.



# OAuth resource-server authentication

The MCP server can act as an OAuth 2.0 protected resource ([RFC 9728](https://www.rfc-editor.org/rfc/rfc9728)): it publishes discovery metadata, lets you declare which OAuth scopes each tool requires, and, on Self-Managed clusters, can validate a Cross-Application Access (XAA) token on incoming requests. All of it is opt-in&mdash;with no OAuth environment variables set, the server behaves as it always has, relying on the DataRobot gateway to authenticate requests.

## Well-known endpoint

The server publishes protected-resource metadata at `/.well-known/oauth-protected-resource` so MCP clients and agents can discover how to authenticate. By default this route requires the same DataRobot-gateway authentication as every other route.

Set `MCP_ENABLE_UNAUTHENTICATED_WELL_KNOWN_ROUTE=true` to serve it without authentication instead. Agents fetch this route before they hold a token, so Cross-Application Access discovery requires it enabled. This is only the server-side half of the switch: the cluster hosting the deployment must also permit unauthenticated access to that path, or anonymous requests never reach the server. This capability is for Self-Managed (single-tenant) clusters.

```bash
MCP_ENABLE_UNAUTHENTICATED_WELL_KNOWN_ROUTE=true
```

## Protected-resource metadata

These variables populate fields in the published document. Lists are comma-separated.

| Variable | Description |
|---|---|
| `MCP_OAUTH_RESOURCE` | The resource identifier (`resource` field). Defaults to a URL built from the container's own runtime identity; set explicitly when only an internal address is reachable. |
| `MCP_OAUTH_AUTHORIZATION_SERVERS` | Authorization server URL(s) clients should use. |
| `MCP_OAUTH_AUDIENCE` | Overrides the expected token audience, for issuers that mint an `aud` different from `MCP_OAUTH_RESOURCE`. |
| `MCP_OAUTH_JWKS_URI` | Overrides the JWKS location, for issuers that don't keep keys at `<issuer>/v1/keys`. |

`scopes_supported` is published automatically&mdash;it's derived from the scope requirements you declare below, so there's nothing to keep in sync by hand.

## Declaring required scopes per tool

You can require OAuth scopes on a tool two ways.

**In code**, with `require_scopes` on the tool's own decorator:

```python
from datarobot_genai.drmcp import dr_mcp_tool, require_scopes


@dr_mcp_tool(auth=require_scopes("mcp:tools:write"))
async def my_custom_tool(...):
    ...
```

All listed scopes are required, not any one of them.

**In configuration**, with one environment variable per tool tag&mdash;the suffix is a tag the tool already declares via `tags={...}`, matched case- and dash-insensitively:

```bash
MCP_OAUTH_TAG_SCOPES_DATABASE=mcp:tools:execute,mcp:tools:database:write
MCP_OAUTH_TAG_SCOPES_READONLY=mcp:tools:read,mcp:resources:read
```

`MCP_OAUTH_SCOPE_SOURCE` controls which mechanism is live. It defaults to `both`, where each mechanism applies wherever it's declared:

| Value | Behavior |
|---|---|
| `both` (default) | Both in-code and tag-based declarations apply. |
| `code` | Only the in-code `require_scopes(...)` declarations apply. |
| `tags` | Only the `MCP_OAUTH_TAG_SCOPES_*` variables apply. |

## Cross-Application Access (XAA)

Cross-Application Access lets an agent read its authorization details from this server's published metadata instead of its own configuration. Publishing the `cross_application_access` block is all-or-nothing: set every one of the four required variables, or the deployment fails.

```bash
MCP_XAA_TRUSTED_ISSUER=https://trusted_issuer_url_used_in_xaa_token_exchange_step
MCP_XAA_EXCHANGE_AUDIENCE=https://url_of_auth_server_with_audience_id
MCP_XAA_TOKEN_URL=https://auth_server_token_request_url
MCP_XAA_SCOPES=scope_to_be_authorized_by_authorization_server
```

Two more variables are optional:

| Variable | Description |
|---|---|
| `MCP_XAA_TOKEN_AUDIENCE` | The audience XAA tokens should carry. Can be omitted when the identity provider doesn't check it. |
| `MCP_XAA_TOKEN_ENDPOINT_AUTH_METHOD` | Token endpoint authentication method. `private_key_jwt` is the only method implemented today. |

## Claim validation

`MCP_ENABLE_OAUTH_CLAIM_VALIDATION` (default `false`) turns on validation of the XAA token carried in the `x-datarobot-external-access-token` request header. It does not affect the primary DataRobot-gateway authentication on the `Authorization` header&mdash;the gateway already authenticates every request before it reaches the server.

```bash
MCP_ENABLE_OAUTH_CLAIM_VALIDATION=true
```

With it on:

| Condition | Result |
|---|---|
| No `x-datarobot-external-access-token` header, or it isn't a parseable JWT | `401` `invalid_token` |
| The token's `aud` claim is missing, or doesn't exactly match `MCP_XAA_TOKEN_AUDIENCE` (a trailing-slash difference counts as a mismatch) | `403` `invalid_token` |
| A `tools/call` request is missing a scope required by the target tool | `403` `insufficient_scope` |

The health check route and everything under `/.well-known/` are always exempt, regardless of this setting.

This check does not verify the token's signature. Trust in the XAA token comes from the token-exchange step that produced it (the `MCP_XAA_*` settings above), not from re-validating it here. If `MCP_XAA_TOKEN_AUDIENCE` is unset, audience validation is skipped.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Clients can't discover the well-known route (a `401`/`403` on `/.well-known/oauth-protected-resource`) | Set `MCP_ENABLE_UNAUTHENTICATED_WELL_KNOWN_ROUTE=true` *and* confirm the cluster allows unauthenticated access to that path&mdash;both are required. |
| Deployment fails with an incomplete Cross-Application Access error | Set all four required `MCP_XAA_*` variables, or unset them all. |
| A tool call is rejected with `insufficient_scope` | Check the scopes declared via `require_scopes(...)` or `MCP_OAUTH_TAG_SCOPES_<TAG>` for that tool's tags, and confirm `MCP_OAUTH_SCOPE_SOURCE` includes the mechanism you used. |
| A tool call is rejected with `invalid_token` for an audience mismatch | Compare the token's `aud` claim against `MCP_XAA_TOKEN_AUDIENCE` exactly, including trailing slashes. |
| A request fails with `401` even though `MCP_ENABLE_OAUTH_CLAIM_VALIDATION` is off | This flag only gates XAA-header validation; a `401` from elsewhere is a DataRobot-gateway authentication failure on `Authorization` instead. See [MCP client setup](mcp_client_setup.md#troubleshooting). |

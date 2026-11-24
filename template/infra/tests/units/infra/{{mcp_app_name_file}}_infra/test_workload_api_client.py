# Copyright 2026 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from . import app_module

_workload_api_client = app_module("workload_api_client")
WORKLOAD_ARTIFACT_TYPE = _workload_api_client.WORKLOAD_ARTIFACT_TYPE
build_artifact_from_image_uri = _workload_api_client.build_artifact_from_image_uri
_mcp_oauth_configs = app_module("mcp_oauth_configs")
WorkloadArtifactContainerRoute = _mcp_oauth_configs.WorkloadArtifactContainerRoute
_mcp_utils = app_module("mcp_utils")
DR_CREDENTIAL_API_TOKEN_KEY = _mcp_utils.DR_CREDENTIAL_API_TOKEN_KEY


def test_image_uri_pulumi_args_use_the_provider_shape():
    """The provider validates snake_case and calls the credential field credential_id."""
    spec = build_artifact_from_image_uri(
        artifact_name="mcp-server",
        container_name="mcp-server",
        container_port=8080,
        image_uri="registry.example.com/mcp:latest",
        environment_vars=[
            {"name": "MCP_SERVER_NAME", "value": "demo"},
            {
                "name": "SESSION_SECRET_KEY",
                "source": "dr-credential",
                "drCredentialId": "cred-123",
                "key": DR_CREDENTIAL_API_TOKEN_KEY,
            },
        ],
        routes=[
            WorkloadArtifactContainerRoute(
                path="/.well-known/oauth-protected-resource", auth="disabled"
            ).to_dict()
        ],
        readiness_probe_path="/",
    )

    args = spec.to_pulumi_args()

    assert args["name"] == "mcp-server"
    assert args["type"] == WORKLOAD_ARTIFACT_TYPE
    container = args["spec"]["container_groups"][0]["containers"][0]
    assert container["image_uri"] == "registry.example.com/mcp:latest"
    assert container["routes"] == [
        {"path": "/.well-known/oauth-protected-resource", "auth": "disabled"}
    ]
    assert container["readiness_probe"] == {"path": "/", "port": 8080}
    assert container["environment_vars"] == [
        {"name": "MCP_SERVER_NAME", "value": "demo"},
        {
            "name": "SESSION_SECRET_KEY",
            "source": "dr-credential",
            "credential_id": "cred-123",
            "key": DR_CREDENTIAL_API_TOKEN_KEY,
        },
    ]


def test_image_uri_pulumi_args_omit_entrypoints_unless_set():
    spec_without = build_artifact_from_image_uri(
        artifact_name="mcp-server",
        container_name="mcp-server",
        container_port=8080,
        image_uri="registry.example.com/mcp:latest",
    )
    args = spec_without.to_pulumi_args()
    container = args["spec"]["container_groups"][0]["containers"][0]
    assert "entrypoints" not in container
    assert "routes" not in container
    assert "readiness_probe" not in container

    spec_with = build_artifact_from_image_uri(
        artifact_name="mcp-server",
        container_name="mcp-server",
        container_port=8080,
        image_uri="registry.example.com/mcp:latest",
        entrypoints=["python", "-m", "app.main"],
    )
    args = spec_with.to_pulumi_args()
    container = args["spec"]["container_groups"][0]["containers"][0]
    assert container["entrypoints"] == ["python", "-m", "app.main"]

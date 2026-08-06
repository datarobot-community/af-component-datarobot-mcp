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

from unittest.mock import patch

import pytest
import requests

from {{mcp_app_name}}_clients.workload_api_client import (
    WORKLOAD_ARTIFACT_TYPE,
    ArtifactSpecFromImageBuildConfig,
    CodeRef,
    CodeRefDatarobot,
    Container,
    ContainerGroup,
    DockerfileProvided,
    ImageBuildConfig,
    WorkloadArtifactSpecFromImageBuildConfig,
    WorkloadClient,
    build_artifact_from_image_uri,
)


def test_workload_artifact_spec_type_is_service():
    container = Container(
        name="primary",
        primary=True,
        port=8080,
        image_build_config=ImageBuildConfig(
            code_ref=CodeRef(
                type="datarobot",
                provider="datarobot",
                datarobot=CodeRefDatarobot(catalog_id="cat", catalog_version_id="ver"),
            ),
            dockerfile=DockerfileProvided(path="docker/Dockerfile"),
        ),
        environment_vars=[{"name": "FOO", "value": "bar"}],
        routes=[{"path": "/.well-known/oauth-protected-resource", "auth": "required"}],
    )
    spec = WorkloadArtifactSpecFromImageBuildConfig(
        name="mcp-server",
        spec=ArtifactSpecFromImageBuildConfig(
            container_groups=[ContainerGroup(containers=[container])]
        ),
    )
    payload = spec.to_payload()

    assert payload["type"] == WORKLOAD_ARTIFACT_TYPE
    assert "workloadType" not in payload
    build_config = payload["spec"]["containerGroups"][0]["containers"][0][
        "imageBuildConfig"
    ]
    assert build_config["codeRef"]["datarobot"]["catalogId"] == "cat"


def test_image_uri_payload_omits_entrypoints_unless_set():
    spec_without = build_artifact_from_image_uri(
        artifact_name="mcp-server",
        container_name="mcp-server",
        container_port=8080,
        image_uri="registry.example.com/mcp:latest",
    )
    container = spec_without.to_payload()["spec"]["containerGroups"][0]["containers"][0]
    assert "entrypoints" not in container

    spec_with = build_artifact_from_image_uri(
        artifact_name="mcp-server",
        container_name="mcp-server",
        container_port=8080,
        image_uri="registry.example.com/mcp:latest",
        entrypoints=["python", "-m", "app.main"],
    )
    container = spec_with.to_payload()["spec"]["containerGroups"][0]["containers"][0]
    assert container["entrypoints"] == ["python", "-m", "app.main"]


def test_delete_artifact_tolerates_conflict_when_workload_retains_it():
    client = WorkloadClient(endpoint="https://example.com/api/v2", token="token")
    response = requests.Response()
    response.status_code = 409
    response.reason = "Conflict"
    response._content = (
        b'{"detail":"Cannot delete artifact referenced by 1 workload(s)"}'
    )

    with patch.object(client._session, "delete", return_value=response):
        client.delete_artifact("abc")  # must not raise


def test_delete_artifact_raises_on_other_errors():
    client = WorkloadClient(endpoint="https://example.com/api/v2", token="token")
    response = requests.Response()
    response.status_code = 500
    response.reason = "Internal Server Error"
    response._content = b'{"detail":"boom"}'
    response.url = "https://example.com/api/v2/artifacts/abc"
    response.request = requests.Request(method="DELETE", url=response.url).prepare()

    with (
        patch.object(client._session, "delete", return_value=response),
        pytest.raises(requests.HTTPError, match="boom"),
    ):
        client.delete_artifact("abc")


def test_trigger_build_surfaces_response_body_on_422():
    client = WorkloadClient(endpoint="https://example.com/api/v2", token="token")
    response = requests.Response()
    response.status_code = 422
    response.reason = "Unprocessable Entity"
    response._content = b'{"detail":"dockerfile not found in catalog"}'
    response.url = "https://example.com/api/v2/artifacts/abc/builds"
    response.request = requests.Request(method="POST", url=response.url).prepare()

    with (
        patch.object(client._session, "post", return_value=response),
        pytest.raises(requests.HTTPError, match="dockerfile not found in catalog"),
    ):
        client.trigger_build("abc")

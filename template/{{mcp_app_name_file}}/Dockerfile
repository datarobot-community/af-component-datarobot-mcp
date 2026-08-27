# Copyright 2025 DataRobot, Inc.
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

# User configuration
ARG UID=1000
ARG GID=1000
ARG UNAME=appuser

# Pin uv by digest (linux/amd64). Update via: docker buildx imagetools inspect ghcr.io/astral-sh/uv:latest
FROM datarobot/mirror_chainguard_datarobot.com_python-fips:3.12-dev AS builder

COPY --from=ghcr.io/astral-sh/uv@sha256:21fedfa1151bb363a6cb32e4a34a032e26f02b3e9e288a96f126ac27d3b472d6 /uv /uvx /usr/local/bin/

WORKDIR /opt/code
ENV UV_PROJECT=/opt/code \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1

# Dependencies only — all locked packages publish musllinux wheels (no build-base).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-progress --color never

# Remaining build-context files. For custom EE builds, .dockerignore excludes app/
# (serverless ships code separately). Workload-docker bundles app/ via Files catalog.
COPY . .

FROM datarobot/mirror_chainguard_datarobot.com_python-fips:3.12-dev AS runtime

ARG UID
ARG GID
ARG UNAME

# Root by its numeric uid: hadolint DL3066 requires numeric user ids
USER 0

RUN addgroup -g "$GID" "$UNAME" && \
    adduser -D -u "$UID" -G "$UNAME" -s /bin/sh "$UNAME"

WORKDIR /opt/code
ENV HOME=/opt/code \
    PYTHONPATH=/opt/code \
    PATH="/opt/venv/bin:${PATH}"

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/code /opt/code

RUN chown -R "$UNAME:$UNAME" /opt/code /opt/venv

# DL3066 wants a numeric uid, but this user is a build arg and a variable never
# looks numeric to hadolint — acknowledged rather than hardcoding the id.
# hadolint ignore=DL3066
USER $UNAME

EXPOSE 8080

ENTRYPOINT []

# Same entrypoint as workload DEFAULT_ENTRYPOINT — deps are baked in builder.
CMD ["python", "-m", "app.main"]

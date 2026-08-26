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

# Dockerfile for DataRobot MCP Custom Model Execution Environment
FROM datarobot/mirror_chainguard_datarobot.com_python-fips:3.12-dev AS base

ARG UID
ARG GID
ARG UNAME

# Root by its numeric uid: hadolint DL3066 requires numeric user ids
USER 0

# Create group and user
RUN addgroup -g "$GID" "$UNAME" && \
    adduser -D -u "$UID" -G "$UNAME" -s /bin/bash "$UNAME"

# Set working directory
WORKDIR /opt/code
ENV HOME=/opt/code

# Install system dependencies using apk
# hadolint ignore=DL3018
RUN apk add --no-cache \
    build-base \
    curl \
    bash

# Install uv (same tool start_server.sh uses at container startup)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Bake the venv at build time from the lock file, matching what start_server.sh
# expects to find (and re-sync as a fast no-op) when the container starts.
ENV UV_PROJECT=/opt/code \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-progress --color never

# Copy the application code (Pulumi copies mcp files to the build context)
COPY . .

# Make start_server.sh executable and set ownership
RUN chown -R $UNAME:$UNAME /opt/code /opt/venv \
    && chmod +x start_server.sh

# Switch to non-root user
# DL3066 wants a numeric uid, but this user is a build arg and a variable never
# looks numeric to hadolint — acknowledged rather than hardcoding the id.
# hadolint ignore=DL3066
USER $UNAME

# Expose port (adjust if your app uses a different port)
EXPOSE 8080

# Reset inherited ENTRYPOINT (base image sets it to "python")
ENTRYPOINT []

# Set the default command
CMD ["/bin/sh", "/opt/code/start_server.sh"]

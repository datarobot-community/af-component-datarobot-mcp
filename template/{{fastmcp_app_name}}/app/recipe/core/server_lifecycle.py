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

import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP


class RecipeServerLifecycle:
    """
    Manages recipe-specific server lifecycle events.
    This class handles actions that need to be executed before and after server startup.
    """

    def __init__(self) -> None:
        """Initialize the RecipeServerLifecycle manager."""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._mcp: Optional[FastMCP] = None

    async def pre_server_start(self, mcp: FastMCP) -> None:
        """
        Execute actions before the server starts.

        Args:
            mcp: The FastMCP instance that will be started
        """
        self._logger.info("Executing pre-server start recipe actions...")
        self._mcp = mcp
        # Add your pre-server start logic here
        # For example:
        # - Initialize recipe-specific resources
        # - Set up recipe-specific connections

        pass

    async def post_server_start(self, mcp: FastMCP) -> None:
        """
        Execute actions after the server has started.

        Args:
            mcp: The running FastMCP instance
        """
        self._logger.info("Executing post-server start recipe actions...")
        # Add your post-server start logic here
        # For example:
        # - Register additional runtime handlers
        # - Start background tasks
        # - Initialize delayed resources

        pass

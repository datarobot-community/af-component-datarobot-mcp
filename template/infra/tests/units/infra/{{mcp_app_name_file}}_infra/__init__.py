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
"""Unit tests for one MCP app's infra package, ``infra.<app>_infra``.

``<app>`` is this directory's name without ``_infra``, so the tests carry no
templated names and run unchanged for every app the component was applied for.
"""

from importlib import import_module
from pathlib import Path
from types import ModuleType

APP_NAME = Path(__file__).resolve().parent.name.removesuffix("_infra")


def app_module(name: str) -> ModuleType:
    """Import ``infra.<app>_infra.<name>``."""
    return import_module(f"infra.{APP_NAME}_infra.{name}")

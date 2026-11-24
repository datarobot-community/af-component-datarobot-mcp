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

"""Pulumi entry point for one MCP app.

``infra/__main__.py`` imports every module in ``infra/infra/`` and copies its public
names. The code for this app lives in ``<this file's name>_infra/stack.py``; this
module loads it and re-exports its names, so nothing here names the app.
"""

from importlib import import_module
from pathlib import Path

_stack = import_module(f".{Path(__file__).stem}_infra.stack", __package__)
globals().update({k: v for k, v in vars(_stack).items() if not k.startswith("_")})

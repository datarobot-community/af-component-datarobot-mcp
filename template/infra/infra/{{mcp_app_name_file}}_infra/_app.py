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

"""Name of the MCP app this infra package belongs to.

The component can be applied several times in one project, once per MCP app.
Each application gets its own ``infra/infra/<app>_infra/`` package, so the
package's own directory name is the app name. Nothing here is templated.
"""

from pathlib import Path

INFRA_PACKAGE_DIR = Path(__file__).resolve().parent
APP_NAME = INFRA_PACKAGE_DIR.name.removesuffix("_infra")


def assert_no_legacy_user_params(infra_dir: Path = INFRA_PACKAGE_DIR.parent) -> None:
    """Stop if ``infra/infra/<app>_user_params.py`` from an older version is still there.

    The parameters moved to ``infra/infra/<app>_infra/user_params.py``. Nothing reads
    the old file any more, so leaving it would silently drop the user's parameters.
    """
    legacy = infra_dir / f"{APP_NAME}_user_params.py"
    if legacy.exists():
        raise RuntimeError(
            f"{legacy} is no longer read. Move your runtime parameters into "
            f"infra/infra/{APP_NAME}_infra/user_params.py, then delete {legacy.name}."
        )
